function canonicalFactory248($bindings, $runtime) {
  const { vec4, sin, cos, abs, floor, tanh, mod, min, max, step, length, dot, add, subtract } = $runtime.stdlib
  const gl_FragCoord = $runtime.fragCoord
  
  var OCTAVES = $bindings["OCTAVES"];
  var RIDGES = $bindings["RIDGES"];
  var OUTPUT_MODE = $bindings["OUTPUT_MODE"];
  var resolution = $bindings["resolution"];
  var tileOffset = $bindings["tileOffset"];
  var fullResolution = $bindings["fullResolution"];
  var time = $bindings["time"];
  var scale = $bindings["scale"];
  var seed = $bindings["seed"];
  var speed = $bindings["speed"];
  var intensity = $bindings["intensity"];
  var fragColor = new Float32Array([0, 0, 0, 0]);
  function permute (x) {
  	x = $runtime.copy(x);
  	return mod(new $runtime.PooledFloat32Array([((x[0] * 34) + 10) * x[0], ((x[1] * 34) + 10) * x[1], ((x[2] * 34) + 10) * x[2]]), 289);
  };
  function permute_vec4 (x) {
  	x = $runtime.copy(x);
  	return mod(new $runtime.PooledFloat32Array([((x[0] * 34) + 10) * x[0], ((x[1] * 34) + 10) * x[1], ((x[2] * 34) + 10) * x[2], ((x[3] * 34) + 10) * x[3]]), 289);
  };
  function taylorInvSqrt (r) {
  	r = $runtime.copy(r);
  	return new $runtime.PooledFloat32Array([1.7928428649902344 - 0.8537347316741943 * r[0], 1.7928428649902344 - 0.8537347316741943 * r[1], 1.7928428649902344 - 0.8537347316741943 * r[2], 1.7928428649902344 - 0.8537347316741943 * r[3]]);
  };
  function simplex3D (v) {
  	v = $runtime.copy(v);
  	var C = new $runtime.PooledFloat32Array([0.1666666716337204, 0.3333333432674408]);
  	var D = new $runtime.PooledFloat32Array([0, 0.5, 1, 2]);
  	v = new $runtime.PooledFloat32Array([v[0] + (seed) * 0.12710000574588776, v[1] + (seed) * 0.12710000574588776, v[2] + (seed) * 0.12710000574588776]);
  	var i = floor(new $runtime.PooledFloat32Array([v[0] + dot(v, new $runtime.PooledFloat32Array([C[1], C[1], C[1]])), v[1] + dot(v, new $runtime.PooledFloat32Array([C[1], C[1], C[1]])), v[2] + dot(v, new $runtime.PooledFloat32Array([C[1], C[1], C[1]]))]));
  	var x0 = new $runtime.PooledFloat32Array([v[0] - i[0] + dot(i, new $runtime.PooledFloat32Array([C[0], C[0], C[0]])), v[1] - i[1] + dot(i, new $runtime.PooledFloat32Array([C[0], C[0], C[0]])), v[2] - i[2] + dot(i, new $runtime.PooledFloat32Array([C[0], C[0], C[0]]))]);
  	var g = step(new $runtime.PooledFloat32Array([x0[1], x0[2], x0[0]]), x0);
  	var l = new $runtime.PooledFloat32Array([1 - g[0], 1 - g[1], 1 - g[2]]);
  	var i1 = min(g, new $runtime.PooledFloat32Array([l[2], l[0], l[1]]));
  	var i2 = max(g, new $runtime.PooledFloat32Array([l[2], l[0], l[1]]));
  	var x1 = new $runtime.PooledFloat32Array([x0[0] - i1[0] + C[0], x0[1] - i1[1] + C[0], x0[2] - i1[2] + C[0]]);
  	var x2 = new $runtime.PooledFloat32Array([x0[0] - i2[0] + C[1], x0[1] - i2[1] + C[1], x0[2] - i2[2] + C[1]]);
  	var x3 = new $runtime.PooledFloat32Array([x0[0] - D[1], x0[1] - D[1], x0[2] - D[1]]);
  	mod(i, 289).reduce((res,el,i)=>(res[i] = el, res), i);
  	var p = permute_vec4(vec4.add([], permute_vec4(vec4.add([], permute_vec4(new $runtime.PooledFloat32Array([i[2], i[2] + i1[2], i[2] + i2[2], i[2] + 1])).map(function (_) {return _ + i[1];}), new $runtime.PooledFloat32Array([0, i1[1], i2[1], 1]))).map(function (_) {return _ + i[0];}), new $runtime.PooledFloat32Array([0, i1[0], i2[0], 1])));
  	var n_ = 0.1428571492433548;
  	var ns = new $runtime.PooledFloat32Array([n_ * D[3] - D[0], n_ * D[1] - D[2], n_ * D[2] - D[0]]);
  	var j = vec4.subtract([], p, floor(new $runtime.PooledFloat32Array([(p[0] * ns[2]) * ns[2], (p[1] * ns[2]) * ns[2], (p[2] * ns[2]) * ns[2], (p[3] * ns[2]) * ns[2]])).map(function (_) {return 49 * _;}));
  	var x_ = floor(new $runtime.PooledFloat32Array([j[0] * ns[2], j[1] * ns[2], j[2] * ns[2], j[3] * ns[2]]));
  	var y_ = floor(new $runtime.PooledFloat32Array([j[0] - 7 * x_[0], j[1] - 7 * x_[1], j[2] - 7 * x_[2], j[3] - 7 * x_[3]]));
  	var x = new $runtime.PooledFloat32Array([x_[0] * ns[0] + ns[1], x_[1] * ns[0] + ns[1], x_[2] * ns[0] + ns[1], x_[3] * ns[0] + ns[1]]);
  	var y = new $runtime.PooledFloat32Array([y_[0] * ns[0] + ns[1], y_[1] * ns[0] + ns[1], y_[2] * ns[0] + ns[1], y_[3] * ns[0] + ns[1]]);
  	var h = vec4.subtract([], abs(x).map(function (_) {return 1 - _;}), abs(y));
  	var b0 = new $runtime.PooledFloat32Array([x[0], x[1], y[0], y[1]]);
  	var b1 = new $runtime.PooledFloat32Array([x[2], x[3], y[2], y[3]]);
  	var s0 = floor(b0).map(function (_) {return _ * 2;}).map(function (_) {return _ + 1;});
  	var s1 = floor(b1).map(function (_) {return _ * 2;}).map(function (_) {return _ + 1;});
  	var sh = step(h, new $runtime.PooledFloat32Array([0, 0, 0, 0])).map(function (_) {return -_;});
  	var a0 = new $runtime.PooledFloat32Array([b0[0] + s0[0] * sh[0], b0[2] + s0[2] * sh[0], b0[1] + s0[1] * sh[1], b0[3] + s0[3] * sh[1]]);
  	var a1 = new $runtime.PooledFloat32Array([b1[0] + s1[0] * sh[2], b1[2] + s1[2] * sh[2], b1[1] + s1[1] * sh[3], b1[3] + s1[3] * sh[3]]);
  	var p0 = new $runtime.PooledFloat32Array([a0[0], a0[1], h[0]]);
  	var p1 = new $runtime.PooledFloat32Array([a0[2], a0[3], h[1]]);
  	var p2 = new $runtime.PooledFloat32Array([a1[0], a1[1], h[2]]);
  	var p3 = new $runtime.PooledFloat32Array([a1[2], a1[3], h[3]]);
  	var norm = taylorInvSqrt(new $runtime.PooledFloat32Array([dot(p0, p0), dot(p1, p1), dot(p2, p2), dot(p3, p3)]));
  	p0 = new $runtime.PooledFloat32Array([p0[0] * norm[0], p0[1] * norm[0], p0[2] * norm[0]]);
  	p1 = new $runtime.PooledFloat32Array([p1[0] * norm[1], p1[1] * norm[1], p1[2] * norm[1]]);
  	p2 = new $runtime.PooledFloat32Array([p2[0] * norm[2], p2[1] * norm[2], p2[2] * norm[2]]);
  	p3 = new $runtime.PooledFloat32Array([p3[0] * norm[3], p3[1] * norm[3], p3[2] * norm[3]]);
  	var m = max(new $runtime.PooledFloat32Array([dot(x0, x0), dot(x1, x1), dot(x2, x2), dot(x3, x3)]).map(function (_) {return 0.6000000238418579 - _;}), 0);
  	(m[0] = m[0] * m[0], m[1] = m[1] * m[1], m[2] = m[2] * m[2], m[3] = m[3] * m[3], m);
  	return 42 * (dot(new $runtime.PooledFloat32Array([m[0] * m[0], m[1] * m[1], m[2] * m[2], m[3] * m[3]]), new $runtime.PooledFloat32Array([dot(p0, x0), dot(p1, x1), dot(p2, x2), dot(p3, x3)])));
  };
  function fbmSimplex3D (p) {
  	p = $runtime.copy(p);
  	var sum = 0;
  	var amp = 1;
  	var freq = 1;
  	var maxAmp = 0;
  	for (var i = 0; i < OCTAVES; i++) {
  	var n = simplex3D(new $runtime.PooledFloat32Array([p[0] * freq, p[1] * freq, p[2] * freq]));
  	sum += n * amp;
  	maxAmp += amp;
  	freq *= 2;
  	amp *= 0.5;
  	};
  	return sum / maxAmp;
  };
  function curlNoise3D (p) {
  	p = $runtime.copy(p);
  	var eps = 1;
  	var a = ((sin(time * 6.283180236816406)) * (speed) + 1) / (OCTAVES) * 0.20000000298023224;
  	var b = ((cos(time * 6.283180236816406)) * (speed) + 1) / (OCTAVES) * 0.20000000298023224;
  	var offset1 = new $runtime.PooledFloat32Array([a, b, 0]);
  	var offset2 = new $runtime.PooledFloat32Array([31.416000366210938 - a, 47.85300064086914 - b, 12.793000221252441]);
  	var offset3 = new $runtime.PooledFloat32Array([93.71900177001953 - b, 61.24800109863281 - a, 73.56099700927734]);
  	var Fx_py = fbmSimplex3D(new $runtime.PooledFloat32Array([p[0] - offset1[0], p[1] + eps - offset1[1], p[2] - offset1[2]]));
  	var Fx_ny = fbmSimplex3D(new $runtime.PooledFloat32Array([p[0] + offset1[0], p[1] - eps + offset1[1], p[2] + offset1[2]]));
  	var Fx_pz = fbmSimplex3D(new $runtime.PooledFloat32Array([p[0] - offset1[0], p[1] - offset1[1], p[2] + eps - offset1[2]]));
  	var Fx_nz = fbmSimplex3D(new $runtime.PooledFloat32Array([p[0] + offset1[0], p[1] + offset1[1], p[2] - eps + offset1[2]]));
  	var Fy_px = fbmSimplex3D(new $runtime.PooledFloat32Array([p[0] + eps - offset2[0], p[1] - offset2[1], p[2] - offset2[2]]));
  	var Fy_nx = fbmSimplex3D(new $runtime.PooledFloat32Array([p[0] - eps + offset2[0], p[1] + offset2[1], p[2] + offset2[2]]));
  	var Fy_pz = fbmSimplex3D(new $runtime.PooledFloat32Array([p[0] - offset2[0], p[1] - offset2[1], p[2] + eps - offset2[2]]));
  	var Fy_nz = fbmSimplex3D(new $runtime.PooledFloat32Array([p[0] + offset2[0], p[1] + offset2[1], p[2] - eps + offset2[2]]));
  	var Fz_px = fbmSimplex3D(new $runtime.PooledFloat32Array([p[0] + eps - offset3[0], p[1] - offset3[1], p[2] - offset3[2]]));
  	var Fz_nx = fbmSimplex3D(new $runtime.PooledFloat32Array([p[0] - eps + offset3[0], p[1] + offset3[1], p[2] + offset3[2]]));
  	var Fz_py = fbmSimplex3D(new $runtime.PooledFloat32Array([p[0] - offset3[0], p[1] + eps - offset3[1], p[2] - offset3[2]]));
  	var Fz_ny = fbmSimplex3D(new $runtime.PooledFloat32Array([p[0] + offset3[0], p[1] - eps + offset3[1], p[2] + offset3[2]]));
  	var dFx_dy = (Fx_py - Fx_ny) / (2 * eps);
  	var dFx_dz = (Fx_pz - Fx_nz) / (2 * eps);
  	var dFy_dx = (Fy_px - Fy_nx) / (2 * eps);
  	var dFy_dz = (Fy_pz - Fy_nz) / (2 * eps);
  	var dFz_dx = (Fz_px - Fz_nx) / (2 * eps);
  	var dFz_dy = (Fz_py - Fz_ny) / (2 * eps);
  	return new $runtime.PooledFloat32Array([dFz_dy - dFy_dz, dFx_dz - dFz_dx, dFy_dx - dFx_dy]);
  };
  function main () {
  	var globalCoord = new $runtime.PooledFloat32Array([gl_FragCoord[0] + tileOffset[0], gl_FragCoord[1] + tileOffset[1]]);
  	var uv = new $runtime.PooledFloat32Array([globalCoord[0] / fullResolution[0], globalCoord[1] / fullResolution[1]]);
  	var aspect = fullResolution[0] / fullResolution[1];
  	var centered = new $runtime.PooledFloat32Array([(uv[0] - 0.5) * aspect, (uv[1] - 0.5)]);
  	var p = new $runtime.PooledFloat32Array([centered[0] * (21 - scale), centered[1] * (21 - scale), 0.5]);
  	var curl = curlNoise3D(p);
  	var cpu_vector_assignment_0 = new $runtime.PooledFloat32Array([(tanh(curl[0] * intensity)) * 0.5 + 0.5, (tanh(curl[1] * intensity)) * 0.5 + 0.5, (tanh(curl[2] * intensity)) * 0.5 + 0.5]);
  	(curl[0] = cpu_vector_assignment_0[0], curl[1] = cpu_vector_assignment_0[1], curl[2] = cpu_vector_assignment_0[2], curl);
  	var color = new $runtime.PooledFloat32Array([0, 0, 0]);
  	if (OUTPUT_MODE == 0) {
  	(color[0] = curl[0], color[1] = curl[0], color[2] = curl[0], color);
  	} else {
  	if (OUTPUT_MODE == 1) {
  	(color[0] = curl[1], color[1] = curl[1], color[2] = curl[1], color);
  	} else {
  	if (OUTPUT_MODE == 2) {
  	(color[0] = curl[2], color[1] = curl[2], color[2] = curl[2], color);
  	} else {
  	if (OUTPUT_MODE == 3) {
  	(color[0] = curl[0], color[1] = curl[1], color[2] = curl[2], color);
  	} else {
  	var curlCentered = new $runtime.PooledFloat32Array([curl[0] * 2 - 1, curl[1] * 2 - 1, curl[2] * 2 - 1]);
  	var mag = length(curlCentered);
  	(color[0] = mag, color[1] = mag, color[2] = mag, color);
  	};
  	};
  	};
  	};
  	if (RIDGES) {
  	abs(new $runtime.PooledFloat32Array([color[0] * 2 - 1, color[1] * 2 - 1, color[2] * 2 - 1])).map(function (_) {return 1 - _;}).reduce((res,el,i)=>(res[i] = el, res), color);
  	};
  	(fragColor[0] = color[0], fragColor[1] = color[1], fragColor[2] = color[2], fragColor[3] = 1, fragColor);
  };
  return function canonicalKernel(context, out) {
    $runtime.beginPixel(context)
    main()
    $runtime.writeColor(fragColor, out)
  }
}
