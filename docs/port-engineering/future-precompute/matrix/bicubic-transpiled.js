
var fragColor = new Float32Array([0, 0, 0, 0]);
var tex = $bindings["tex"];
var resolution = $bindings["resolution"];
function f (p) {
	p = p.slice();
	return texture(tex, new Float32Array([p[0] / resolution[0], p[1] / resolution[1]]))[0];
};
function bicubic (p) {
	p = p.slice();
	var x = p[0];
	var y = p[1];
	var x1 = floor(x);
	var y1 = floor(y);
	var x2 = x1 + 1.;
	var y2 = y1 + 1.;
	var f11 = f(new Float32Array([x1, y1]));
	var f12 = f(new Float32Array([x1, y2]));
	var f21 = f(new Float32Array([x2, y1]));
	var f22 = f(new Float32Array([x2, y2]));
	var f11x = (f(new Float32Array([x1 + 1., y1])) - f(new Float32Array([x1 - 1., y1]))) / 2.;
	var f12x = (f(new Float32Array([x1 + 1., y2])) - f(new Float32Array([x1 - 1., y2]))) / 2.;
	var f21x = (f(new Float32Array([x2 + 1., y1])) - f(new Float32Array([x2 - 1., y1]))) / 2.;
	var f22x = (f(new Float32Array([x2 + 1., y2])) - f(new Float32Array([x2 - 1., y2]))) / 2.;
	var f11y = (f(new Float32Array([x1, y1 + 1.])) - f(new Float32Array([x1, y1 - 1.]))) / 2.;
	var f12y = (f(new Float32Array([x1, y2 + 1.])) - f(new Float32Array([x1, y2 - 1.]))) / 2.;
	var f21y = (f(new Float32Array([x2, y1 + 1.])) - f(new Float32Array([x2, y1 - 1.]))) / 2.;
	var f22y = (f(new Float32Array([x2, y2 + 1.])) - f(new Float32Array([x2, y2 - 1.]))) / 2.;
	var f11xy = (f(new Float32Array([x1 + 1., y1 + 1.])) - f(new Float32Array([x1 + 1., y1 - 1.])) - f(new Float32Array([x1 - 1., y1 + 1.])) + f(new Float32Array([x1 - 1., y1 - 1.]))) / 4.;
	var f12xy = (f(new Float32Array([x1 + 1., y2 + 1.])) - f(new Float32Array([x1 + 1., y2 - 1.])) - f(new Float32Array([x1 - 1., y2 + 1.])) + f(new Float32Array([x1 - 1., y2 - 1.]))) / 4.;
	var f21xy = (f(new Float32Array([x2 + 1., y1 + 1.])) - f(new Float32Array([x2 + 1., y1 - 1.])) - f(new Float32Array([x2 - 1., y1 + 1.])) + f(new Float32Array([x2 - 1., y1 - 1.]))) / 4.;
	var f22xy = (f(new Float32Array([x2 + 1., y2 + 1.])) - f(new Float32Array([x2 + 1., y2 - 1.])) - f(new Float32Array([x2 - 1., y2 + 1.])) + f(new Float32Array([x2 - 1., y2 - 1.]))) / 4.;
	var Q = new Float32Array([f11, f21, f11x, f21x, f12, f22, f12x, f22x, f11y, f21y, f11xy, f21xy, f12y, f22y, f12xy, f22xy]);
	var S = new Float32Array([1., 0., 0., 0., 0., 0., 1., 0., -3., 3., -2., -1., 2., -2., 1., 1.]);
	var T = new Float32Array([1., 0., -3., 2., 0., 0., 3., -2., 0., 1., -2., 1., 0., 0., -1., 1.]);
	var A = matrixMult(matrixMult(T, Q), S);
	var t = fract(p[0]);
	var u = fract(p[1]);
	var tv = new Float32Array([1., t, t * t, (t * t) * t]);
	var uv4 = new Float32Array([1., u, u * u, (u * u) * u]);
	var result = dot(new Float32Array([dot(tv, new Float32Array([A[0], A[1], A[2], A[3]])), dot(tv, new Float32Array([A[4], A[5], A[6], A[7]])), dot(tv, new Float32Array([A[8], A[9], A[10], A[11]])), dot(tv, new Float32Array([A[12], A[13], A[14], A[15]]))]), uv4);
	return result;
};
function main () {
	new Float32Array([bicubic(new Float32Array([3.0, 4.0])), bicubic(new Float32Array([3.0, 4.0])), bicubic(new Float32Array([3.0, 4.0])), bicubic(new Float32Array([3.0, 4.0]))]).reduce((res,el,i)=>(res[i] = el, res), fragColor);
};