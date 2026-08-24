
var fragColor = new Float32Array([0, 0, 0, 0]);
var inputColor = $bindings["inputColor"];
var fwdA = new Float32Array([1.0, 1.0, 1.0, 0.3963377774, -0.1055613458, -0.0894841775, 0.2158037573, -0.0638541728, -1.2914855480]);
var fwdB = new Float32Array([4.0767245293, -1.2681437731, -0.0041119885, -3.3072168827, 2.6093323231, -0.7034763098, 0.2307590544, -0.3411344290, 1.7068625689]);
var invB = new Float32Array([0.4121656120, 0.2118591070, 0.0883097947, 0.5362752080, 0.6807189584, 0.2818474174, 0.0514575653, 0.1074065790, 0.6302613616]);
var invA = new Float32Array([0.2104542553, 1.9779984951, 0.0259040371, 0.7936177850, -2.4285922050, 0.7827717662, -0.0040720468, 0.4505937099, -0.8086757660]);
function oklab_from_linear_srgb (c) {
	c = c.slice();
	var lms = new Float32Array([invB[0] * c[0] + invB[3] * c[1] + invB[6] * c[2], invB[1] * c[0] + invB[4] * c[1] + invB[7] * c[2], invB[2] * c[0] + invB[5] * c[1] + invB[8] * c[2]]);
	return (vec3.multiply([], sign(lms), pow(abs(lms), new Float32Array([0.3333333333333, 0.3333333333333, 0.3333333333333])))).map(function (x, i, v) { var sum = 0; for (var j = 0; j < 3; j++) {sum += this[j*3+i] * v[j]} return sum; }, invA);
};
function linear_srgb_from_oklab (c) {
	c = c.slice();
	var lms = new Float32Array([fwdA[0] * c[0] + fwdA[3] * c[1] + fwdA[6] * c[2], fwdA[1] * c[0] + fwdA[4] * c[1] + fwdA[7] * c[2], fwdA[2] * c[0] + fwdA[5] * c[1] + fwdA[8] * c[2]]);
	return (new Float32Array([(lms[0] * lms[0]) * lms[0], (lms[1] * lms[1]) * lms[1], (lms[2] * lms[2]) * lms[2]])).map(function (x, i, v) { var sum = 0; for (var j = 0; j < 3; j++) {sum += this[j*3+i] * v[j]} return sum; }, fwdB);
};
function main () {
	var lab = oklab_from_linear_srgb(inputColor);
	var back = linear_srgb_from_oklab(lab);
	(fragColor[0] = back[0], fragColor[1] = back[1], fragColor[2] = back[2], fragColor[3] = 1, fragColor);
};