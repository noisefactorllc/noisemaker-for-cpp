// Test-only filesystem responses for explicitly registered ordinary placeholders.
const fs = require('node:fs');
const {resolve, sep} = require('node:path');
const {fileURLToPath} = require('node:url');
const {syncBuiltinESMExports} = require('node:module');
const links = new Map(Object.entries(JSON.parse(process.env.NOISEMAKER_TEST_LINKS || '{}')));
const pathString = p => resolve(p instanceof URL ? fileURLToPath(p) : String(p));
function redirected(p) {
  const path = pathString(p);
  for (const [link, target] of links) {
    if (path === link || path.startsWith(link + sep)) return target + path.slice(link.length);
  }
  return p;
}
function linkStats(stats) {
  return new Proxy(stats, {get(object, key) {
    if (key === 'mode') return (object.mode & ~fs.constants.S_IFMT) | fs.constants.S_IFLNK;
    if (key === 'isSymbolicLink') return () => true;
    if (key === 'isDirectory' || key === 'isFile') return () => false;
    const value = Reflect.get(object, key);
    return typeof value === 'function' ? value.bind(object) : value;
  }});
}
const originalLstat = fs.lstatSync.bind(fs);
fs.lstatSync = (p, ...args) => links.has(pathString(p))
  ? linkStats(originalLstat(p, ...args)) : originalLstat(redirected(p), ...args);
const originalPromiseLstat = fs.promises.lstat.bind(fs.promises);
fs.promises.lstat = async (p, ...args) => links.has(pathString(p))
  ? linkStats(await originalPromiseLstat(p, ...args)) : originalPromiseLstat(redirected(p), ...args);
const originalCallbackLstat = fs.lstat.bind(fs);
fs.lstat = (p, ...args) => {
  const callback = args.pop();
  return originalCallbackLstat(links.has(pathString(p)) ? p : redirected(p), ...args,
    (error, stats) => callback(error, !error && links.has(pathString(p)) ? linkStats(stats) : stats));
};
for (const name of ['realpath', 'stat', 'readFile', 'access', 'readdir']) {
  const original = fs[name].bind(fs);
  fs[name] = (p, ...args) => original(redirected(p), ...args);
  const originalSync = fs[name + 'Sync'].bind(fs);
  fs[name + 'Sync'] = (p, ...args) => originalSync(redirected(p), ...args);
  const originalPromise = fs.promises[name].bind(fs.promises);
  fs.promises[name] = (p, ...args) => originalPromise(redirected(p), ...args);
}
syncBuiltinESMExports();
