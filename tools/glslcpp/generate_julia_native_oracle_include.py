#!/usr/bin/env python3
"""Fail-closed materializer for the authenticated Julia CPU oracle."""
from __future__ import annotations
import argparse, copy, hashlib, json, math, pathlib, re, sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
PACKAGE = ROOT / "docs/port-engineering/julia-parity"
ORACLE = PACKAGE / "julia-oracles.json"
TARGET = ROOT / "tests/oracles/julia_expected.inc"
SCHEMA = "noisemaker-for-cpp.julia.pixel-parity.v1"
KEY = "synth/julia:julia"
SOURCE = "tools/glslcpp/corpus/a024dc3a960cc44af454abc7aebce50456c194e6/sources/synth/julia/julia.glsl"
SOURCE_SHA = "825e175c22fea086ad2860e16bcf0a79d797574a9dfad937a23baaadaffdeef0"
FACTORY_SOURCE = "src/effects/adapters/julia.js"
FACTORY_SOURCE_SHA = "0f9cc65f966a358bc4671399e8de49d144d0272a07ef2ae15a0bfb57048eadd5"
FACTORY_SHA = "ed39921d1b85c59d7c86caa715c50987525bc9bcc6903a885810f133480545d6"
GENERATOR_RELATIVE = "docs/port-engineering/julia-parity/julia_oracle_generator.mjs"
MATERIALIZER_RELATIVE = "tools/glslcpp/generate_julia_native_oracle_include.py"
GENERATOR_SHA = "4445d39ddc05e720d2583d0b1cf785434464c1e764eb3059f20da65165158017"
CORPUS = "a024dc3a960cc44af454abc7aebce50456c194e6"
UPSTREAM = "117a236679d1db3ab8f0e278230ece277b57564c"
EXPECTED_NAMES = ["resolution", "tileOffset", "fullResolution", "time", "cReal", "cImag", "poi", "outputMode", "centerX", "centerY", "rotation", "iterations", "stripeFreq", "trapShape", "lightAngle", "cPath", "cSpeed", "cRadius", "invert", "zoomSpeed", "zoomDepth"]
EXPECTED_ABI = {"resolution":"Vec2", "tileOffset":"Vec2", "fullResolution":"Vec2", "time":"number", "cReal":"number", "cImag":"number", "poi":"int32", "outputMode":"int32", "centerX":"number", "centerY":"number", "rotation":"number", "iterations":"int32", "stripeFreq":"number", "trapShape":"int32", "lightAngle":"number", "cPath":"int32", "cSpeed":"number", "cRadius":"number", "invert":"bool", "zoomSpeed":"number", "zoomDepth":"number"}
EXPECTED_SOURCE_ABI = {"resolution":"vec2", "tileOffset":"vec2", "fullResolution":"vec2", "time":"float", "cReal":"float", "cImag":"float", "poi":"int", "outputMode":"int", "centerX":"float", "centerY":"float", "rotation":"float", "iterations":"int", "stripeFreq":"float", "trapShape":"int", "lightAngle":"float", "cPath":"int", "cSpeed":"float", "cRadius":"float", "invert":"bool", "zoomSpeed":"float", "zoomDepth":"float"}
EXPECTED_CLOSURE = {"src/csl/glsl-kernel.js":"a684b1bc16f095c550e488d1db35b9cea9c69b761db6ad3af175110e6a2e2baa", "src/csl/glsl-runtime.js":"a20421c56aa3274746f6887555445b8c7f7bb8318921fe6f75f6aa8ffe71c072", "src/csl/runtime.js":"a34ac04d63bb0865081ad3964b1ff5a427664a80e35f43c1761d91b0ea8e7dee", "src/effects/adapters/bit-effects.js":"5044fc318e69deb1e03330f977af1f8a76376c69936ebf0a6d33fe350379d7c7", "src/effects/adapters/crt.js":"c424c45169894e1d39eb11dc97c1835991fa9e990f3dd7c1aeefafbfe9f3a5cc", "src/effects/adapters/f32-color.js":"b0d2562969029701f44b049dbfa17fc7a13f97758c3750f05ad57a836269b046", "src/effects/adapters/fractal.js":"0c90d859a589d4bfd0f9a82b2f601675b6116671e20b2dfba9bab2b98fc72a29", "src/effects/adapters/index.js":"40c690ff6ef58619006d0819c5f0f4d419cdfd59a08db55e2276aa9f61430267", "src/effects/adapters/julia.js":FACTORY_SOURCE_SHA, "src/effects/adapters/median.js":"e82f18d820533993f74c3436addd8bb271a3ef0db8a53c6771ba4eb1e90b0583", "src/effects/adapters/palette.js":"8b7c83ea52c3be218866570517335141f9203905115fc90d2e69b1d8cba54452", "src/effects/adapters/snow.js":"202e0dbf9b1b8e0e7278c87527d6e2b740eb0a23385115c4805a389caab96366", "src/effects/catalog.js":"d8cf312294ccd915892a4a668432ca2533ab255fb24664d89dee8456331e4ea4", "src/effects/definition.js":"fdade0a1f2ab0773b08b9778807d9901583a540c409a9a275cf2fc1c67f6af02", "src/effects/generated/canonical-adapter-data.js":"ca0b139d776f9433b72534f58df9ff182ec55369e85ce37d422990dc0184baab", "src/effects/generated/canonical-kernels.js":"66adc01c7df07298b40eaf74fddb7226fdf87bb18dea75b527640c88d0f40ebe", "src/effects/generated/kernels.js":"b535b989f0f130c44261815d90678deb9996ab3098bb8d1cb5591a8f8d8d3c01", "src/effects/generated/upstream-snapshot.js":"e8f8a421f08b0f5cb495f845a97da321038300b7d0dd41392a60653ce2a82090", "src/effects/registry.js":"8b3eac7fd4df8699bf27995987eb534625adbce5fe7aa432649a83f278af9618", "src/runtime/pass-runner.js":"fbfd53470735a07dca317c384b9985bb55383961199815e67aee9adda7e881aa", "src/runtime/sampler.js":"1e7dc92a20de983ce8b4afd03f3ea83bc86c010e622c4edc4a0aa702027ed328", "src/runtime/surface.js":"0cd69c920a710f636a5208e05b49633fc2747cdc2f5fc61113433ceb9ec8ba59"}
EXACTNESS = {"float32":"raw little-endian uint32 words; signed zero and NaN payloads significant", "rgba8":"complete independently captured RGBA8 bytes", "tolerance":"none", "dimensions":"checked before lane access", "comparison":"dimensions, counts, every uint32 word, every RGBA8 byte"}
COMPARER = {"dimensions_before_access":True, "first_mismatch_reported":True, "raw_words_and_rgba8_independent":True, "cases":{"good":True,"dimensions":True,"short":True,"long":True,"rgba8_count":True,"rgba8_mismatch":True,"signed_zero":True,"nan_payload":True}}
def _case(name,width,height,controls,input_hash,expected_hash,rgba_hash):
    return {"name":name,"width":width,"height":height,**controls,"input_immutable_exact_bits":True,"alpha_f32_word":"0x3f800000","alpha_rgba8_byte":255,"bindings":{"resolution":[width,height],"tileOffset":[controls["tileX"],controls["tileY"]],"fullResolution":[width,height],**{k:controls[k] for k in EXPECTED_NAMES[3:]}},"input_f32_sha256":input_hash,"expected_f32_sha256":expected_hash,"expected_rgba8_sha256":rgba_hash}
EXPECTED_CASES = [
 _case("manual-smooth",5,4,{"time":0.25,"cReal":-0.123,"cImag":0.745,"poi":0,"outputMode":0,"centerX":-0.1,"centerY":0.05,"rotation":0,"iterations":80,"stripeFreq":0,"trapShape":0,"lightAngle":30,"cPath":0,"cSpeed":0,"cRadius":0.5,"invert":False,"zoomSpeed":0,"zoomDepth":1,"tileX":0,"tileY":0,"salt":1},"04ec1b2e75cba0252250ddb7c2015a6866b7b62c6073d4fbf00edda49a77a1cb","68ce3ccc4770b082b0ca69e38a2dff21faf781a4627e582ab05cc611e6ad5508","b1afc3dbe46c96d9627c89a90caea13bd4d5768cdc9929dcddb759fc39b5d1fa"),
 _case("manual-distance-tile",4,5,{"time":0.75,"cReal":0.28,"cImag":0.008,"poi":0,"outputMode":1,"centerX":0,"centerY":0,"rotation":12,"iterations":120,"stripeFreq":0,"trapShape":0,"lightAngle":60,"cPath":0,"cSpeed":0,"cRadius":0.5,"invert":False,"zoomSpeed":0,"zoomDepth":1,"tileX":0.5,"tileY":-0.25,"salt":2},"e0f86664cee61f34fcde6f54e7f5409e68d9383f86fbdd328df64321f537f05c","2420f5e9856fb635232e4025ed4d56c7ff00f46a9ff392992883f9db311a0e6a","6350bb261836336ff3b357cbeb7a1c3438c0ffa2c093efe1316ce3d1e8b98a04"),
 _case("manual-stripe",6,3,{"time":1.5,"cReal":0.28,"cImag":0.008,"poi":0,"outputMode":2,"centerX":0,"centerY":0,"rotation":0,"iterations":90,"stripeFreq":2.75,"trapShape":1,"lightAngle":120,"cPath":0,"cSpeed":0,"cRadius":0.5,"invert":False,"zoomSpeed":0,"zoomDepth":1,"tileX":0,"tileY":0,"salt":3},"696e64435afb893bf92064201a0a8317209ec4e05cc93d73931087777bc23847","1194a269b70b781d38398a4f2c46e4dbf18061dfe8d9e4a1c26fc401a7b76f85","cc4cb3f21a2715c0383b0a024d1b613eff3354f064dd5d763e61c57ea93589f3"),
 _case("poi-trap",5,5,{"time":2,"cReal":0,"cImag":0,"poi":7,"outputMode":3,"centerX":0.1,"centerY":-0.1,"rotation":0,"iterations":150,"stripeFreq":0,"trapShape":2,"lightAngle":210,"cPath":0,"cSpeed":0,"cRadius":0.5,"invert":False,"zoomSpeed":1.25,"zoomDepth":8,"tileX":-0.375,"tileY":0.625,"salt":4},"ac3df82128d83e2e89260464cfbb004457912bb155a5eb972f74717e3907c7e5","75352c0017ab1e77ff8eb69b000c8758e33ea992d501ee74b15034f5a84a997f","da6f14970ce356ce01a5b340291e9d8b2652eb63fbf8f328ca6a87a727fde4d9"),
 _case("manual-normal",4,4,{"time":3.25,"cReal":-0.8,"cImag":0.156,"poi":0,"outputMode":4,"centerX":-0.25,"centerY":0.01,"rotation":-18,"iterations":64,"stripeFreq":0,"trapShape":0,"lightAngle":300,"cPath":0,"cSpeed":0,"cRadius":0.5,"invert":False,"zoomSpeed":0,"zoomDepth":2,"tileX":0,"tileY":0,"salt":5},"0cf32eaaf33b72ee8475938c52a05f7a3b757296f4532fb63743948faf9fec50","a48b5c5dfb26c1525ec288ea6dd6f09734e204437fde85b0d1681ac4733c1dca","7db70c0ff3cb9d1760bcbe349ff2f3cd4e374680720d96dffaf52b65fb48ac7a"),
 _case("animated-circle",4,3,{"time":0.5,"cReal":0,"cImag":0,"poi":0,"outputMode":0,"centerX":0.3,"centerY":0.4,"rotation":0,"iterations":64,"stripeFreq":0,"trapShape":0,"lightAngle":45,"cPath":2,"cSpeed":0.75,"cRadius":0.55,"invert":False,"zoomSpeed":0,"zoomDepth":1,"tileX":0,"tileY":0,"salt":6},"354b8e6e312ddf00b3d4bc2f734c506ad24a9c0c48df6ba6f23890443119040f","e24ee7903037973363d2ac465310ae2ad5f67321352811f8a40e03904c69bb83","f5656fbf77f179e0b98440ab8e06bd87debbc5bdddf60d661e395bef58ee1899"),
 _case("invert-output",3,4,{"time":1.1,"cReal":-0.7455,"cImag":0.113,"poi":0,"outputMode":1,"centerX":0,"centerY":0,"rotation":25,"iterations":96,"stripeFreq":0,"trapShape":0,"lightAngle":90,"cPath":0,"cSpeed":0,"cRadius":0.5,"invert":True,"zoomSpeed":0,"zoomDepth":2,"tileX":0,"tileY":0,"salt":7},"58ab9329ff6a09a1179c3580f8a787da461583678ecc6dee47f24c000fed568d","c90489868a1a64a74239d5331b18d608ef69e28579f36f3ae1949cfe7354907a","80a76a18acf8cb64fec3a659ffc4bab4a87cd9a6fde4dab2161a8751d136c9d2"),
 _case("animated-lissajous",3,3,{"time":0.9,"cReal":0,"cImag":0,"poi":0,"outputMode":3,"centerX":0,"centerY":0,"rotation":-12,"iterations":72,"stripeFreq":0,"trapShape":1,"lightAngle":180,"cPath":1,"cSpeed":1.1,"cRadius":0.4,"invert":False,"zoomSpeed":0.8,"zoomDepth":3,"tileX":0.25,"tileY":-0.5,"salt":8},"a0c51cd0aa9ad8a182b9d62fd6205b2339e03f1430b49cb37e56a6d70fec75e3","8657f768505e95acfcb2802903768a6bf4e72e408ddea917bc9780784ffd2c44","d574fbbbc44a56d8ec9bf06a4221e0c975b101e434c87e030572be6660dfb538"),
 _case("iterations-min",1,1,{"time":0,"cReal":0,"cImag":0,"poi":0,"outputMode":0,"centerX":0,"centerY":0,"rotation":0,"iterations":1,"stripeFreq":0,"trapShape":0,"lightAngle":45,"cPath":0,"cSpeed":0,"cRadius":0.5,"invert":False,"zoomSpeed":0,"zoomDepth":1,"tileX":0,"tileY":0,"salt":9},"9ab27ec849e1d15f5c1b80a7c88f41b3be7c10af6e8fdf00649fd5a45f183c76","7ab8f6c26e4f9862c95a18c8e5c50403eeb64d8869fbbf9a7a6397d9a63b7b0e","e3820096cb82366b860b8a4e668453a7aaaf423af03bdf289fa308ea03a79332"),
 _case("iterations-max",1,1,{"time":6.4456087906019786,"cReal":0.7145556327222278,"cImag":0.18602843191149376,"poi":0,"outputMode":3,"centerX":-0.5526962232665849,"centerY":-0.20907021993982378,"rotation":-24.482864887566052,"iterations":1000,"stripeFreq":0,"trapShape":0,"lightAngle":284.247223381942,"cPath":3,"cSpeed":1.1909674250499735,"cRadius":0.8099422763590567,"invert":False,"zoomSpeed":0,"zoomDepth":4.561745525235716,"tileX":0,"tileY":0,"salt":15},"3e528f72f53b49516bb6c44bdd3db8f688f2c0105fa1120e8ea941ca5d88ead2","7ab8f6c26e4f9862c95a18c8e5c50403eeb64d8869fbbf9a7a6397d9a63b7b0e","e3820096cb82366b860b8a4e668453a7aaaf423af03bdf289fa308ea03a79332"),
 _case("iterations-clamp-1001",1,1,{"time":6.4456087906019786,"cReal":0.7145556327222278,"cImag":0.18602843191149376,"poi":0,"outputMode":3,"centerX":-0.5526962232665849,"centerY":-0.20907021993982378,"rotation":-24.482864887566052,"iterations":1001,"stripeFreq":0,"trapShape":0,"lightAngle":284.247223381942,"cPath":3,"cSpeed":1.1909674250499735,"cRadius":0.8099422763590567,"invert":False,"zoomSpeed":0,"zoomDepth":4.561745525235716,"tileX":0,"tileY":0,"salt":15},"3e528f72f53b49516bb6c44bdd3db8f688f2c0105fa1120e8ea941ca5d88ead2","e59c766c5f4c4faface8b7b5e30bafb20c6d10c89c12aba22784010e24fd1b67","118a1615c6cfc6ba1f8f9c5f3a4c07e4f79edd70d13f56c086d7f0c2a655e66b"),
 _case("bulb-path",2,2,{"time":0.25,"cReal":0,"cImag":0,"poi":0,"outputMode":1,"centerX":0,"centerY":0,"rotation":0,"iterations":64,"stripeFreq":0,"trapShape":0,"lightAngle":45,"cPath":3,"cSpeed":0.5,"cRadius":0.5,"invert":False,"zoomSpeed":0,"zoomDepth":1,"tileX":0,"tileY":0,"salt":11},"eaa3484acd7fa41d0ad4941309bab6374f222c210b17764fb521d5cf4eefcb7f","9ba3b531624710dece54456c2e5cb1cb31d7df8cfb6fee2b1180d0cb791ea049","cc0fa51d4d0a97b664030be5052f3b2b69a1267f89ace4c9bbc65007566725df"),
 _case("poi-fallback",2,2,{"time":0.5,"cReal":0.2,"cImag":-0.3,"poi":99,"outputMode":1,"centerX":0,"centerY":0,"rotation":0,"iterations":64,"stripeFreq":0,"trapShape":0,"lightAngle":45,"cPath":0,"cSpeed":0,"cRadius":0.5,"invert":False,"zoomSpeed":0,"zoomDepth":1,"tileX":0,"tileY":0,"salt":12},"7b8fcf38d596b67f0caf52ff4ba76e5a14213cae87d9ee2d7ba8ea354aa19b2d","9ba3b531624710dece54456c2e5cb1cb31d7df8cfb6fee2b1180d0cb791ea049","cc0fa51d4d0a97b664030be5052f3b2b69a1267f89ace4c9bbc65007566725df"),
 _case("period-convergence",1,1,{"time":0,"cReal":0,"cImag":0,"poi":0,"outputMode":3,"centerX":0,"centerY":0,"rotation":0,"iterations":50,"stripeFreq":0,"trapShape":0,"lightAngle":45,"cPath":0,"cSpeed":0,"cRadius":0.5,"invert":False,"zoomSpeed":0,"zoomDepth":1,"tileX":0,"tileY":0,"salt":13},"df5b7da9a846298cb6d8132039eef63d490145aec049791b61256d076cde4877","7ab8f6c26e4f9862c95a18c8e5c50403eeb64d8869fbbf9a7a6397d9a63b7b0e","e3820096cb82366b860b8a4e668453a7aaaf423af03bdf289fa308ea03a79332"),
 _case("fallback-output-mode",5,4,{"time":0.25,"cReal":-0.123,"cImag":0.745,"poi":0,"outputMode":5,"centerX":-0.1,"centerY":0.05,"rotation":0,"iterations":80,"stripeFreq":0,"trapShape":0,"lightAngle":30,"cPath":0,"cSpeed":0,"cRadius":0.5,"invert":False,"zoomSpeed":0,"zoomDepth":1,"tileX":0,"tileY":0,"salt":1},"04ec1b2e75cba0252250ddb7c2015a6866b7b62c6073d4fbf00edda49a77a1cb","68ce3ccc4770b082b0ca69e38a2dff21faf781a4627e582ab05cc611e6ad5508","b1afc3dbe46c96d9627c89a90caea13bd4d5768cdc9929dcddb759fc39b5d1fa"),
 _case("fallback-trap-shape",4,3,{"time":1.5,"cReal":0.28,"cImag":0.008,"poi":0,"outputMode":3,"centerX":0,"centerY":0,"rotation":0,"iterations":90,"stripeFreq":0,"trapShape":9,"lightAngle":120,"cPath":0,"cSpeed":0,"cRadius":0.5,"invert":False,"zoomSpeed":0,"zoomDepth":1,"tileX":0,"tileY":0,"salt":3},"a099727fbe3dc3ca104ec1229bf5ad6d2c537046798fd6a199a6f4db641e9fe3","e1b2ea7b0afff299f71fe14a7e7030191d30ae0b6aa94d6247c0d9480ee37cc3","7b40c20788a3091bcce9e5ad651c7629b9302cfc25d9f35063b62bb8121e311d"),
 _case("fallback-c-path",4,3,{"time":0.5,"cReal":0,"cImag":0,"poi":0,"outputMode":0,"centerX":0.3,"centerY":0.4,"rotation":0,"iterations":64,"stripeFreq":0,"trapShape":0,"lightAngle":45,"cPath":9,"cSpeed":0.75,"cRadius":0.55,"invert":False,"zoomSpeed":0,"zoomDepth":1,"tileX":0,"tileY":0,"salt":6},"354b8e6e312ddf00b3d4bc2f734c506ad24a9c0c48df6ba6f23890443119040f","8cea1b2ba74e80909c56b26a87e7d02eee4517266ae0ab2f34d8fa601d4e2ba8","937d497ff9439479f9a77994b703e6ebced8ca0b9b3c66640567d267c5387a75"),
 _case("non-square-f32-transform",7,3,{"time":1.25,"cReal":-0.4,"cImag":0.6,"poi":0,"outputMode":4,"centerX":0.125,"centerY":-0.2,"rotation":33,"iterations":73,"stripeFreq":0,"trapShape":0,"lightAngle":271,"cPath":0,"cSpeed":0,"cRadius":0.5,"invert":False,"zoomSpeed":0,"zoomDepth":2.5,"tileX":0.375,"tileY":-0.125,"salt":14},"6347d28706b4fa2aaa32f7e6ffb6ad011ee58c9937806df40040149fe5dc2a8f","d87a4033d8f1c820c25ea77bf66190fe4cead0a837704e9eb2acd2942dcdbf59","7f71dc59b8540f092d688fd38421ef3d240c09f4490fd47e175f3cce8d171117"),
]
EXPECTED_ORDER = ['cross-lane-dz-assignment','df64-re2-carrier','df64-im2-carrier','df64-product-carrier','df64-next-re-carrier','out-iteration','out-z-magnitude2','out-derivative-magnitude2','out-stripe-sum','out-stripe-count','out-stripe-last','out-trap-min','transform-re-owner','transform-im-owner','loop-bound','loop-clamp-1001','period-loop-bound','log-smoothing','log-distance','log-stripe','log-stripe-normalization','normal-base','normal-right','normal-up','result-trap-number']
EXPECTED_GROUPS = {"cross-lane-assignment":1,"df64-carrier":4,"out-materialization":10,"iteration-loop":3,"log-sites":4,"normal-three-sample":3}
EXPECTED_MECHANISMS = {'cross-lane-dz-assignment':'replace next-derivative temporary with source-order aliasing','df64-re2-carrier':'replace df64 real-square carrier owner','df64-im2-carrier':'replace df64 imaginary-square carrier owner','df64-product-carrier':'replace df64 product carrier owner','df64-next-re-carrier':'replace df64 next-real carrier owner','out-iteration':'mutate iteration result owner materialization','out-z-magnitude2':'mutate zMagnitude2 result owner materialization','out-derivative-magnitude2':'mutate derivativeMagnitude2 result owner materialization','out-stripe-sum':'mutate stripeSum result owner materialization','out-stripe-count':'mutate stripeCount result owner materialization','out-stripe-last':'mutate stripeLast result owner materialization','out-trap-min':'mutate trapMin result owner materialization','transform-re-owner':'mutate transform real coordinate owner','transform-im-owner':'mutate transform imaginary coordinate owner','loop-bound':'shorten Julia outer iteration bound','loop-clamp-1001':'remove the runtime maxIterations clamp at the direct 1001 boundary','period-loop-bound':'widen period detection convergence bound','log-smoothing':'mutate smooth iteration logarithm','log-distance':'mutate distance estimation logarithm','log-stripe':'mutate stripe logarithm','log-stripe-normalization':'mutate stripe normalization logarithm','normal-base':'mutate normal base sample coordinate','normal-right':'mutate normal right sample coordinate','normal-up':'mutate normal up sample coordinate','result-trap-number':'preserve the JS Number trap accumulator instead of forcing an unsafe Float32 result boundary'}
EXPECTED_ANCHORS = {'cross-lane-dz-assignment':'c83c5e436be035614cc98e1b8e96d71c5a31804e1c543c8e9001b9052ff4e44a','df64-re2-carrier':'8179e52b0d81507ebe5ea947187d17e13369707e41a6724a1c3e9c4718d46333','df64-im2-carrier':'869cd06339a147e9cb452afdaded26b2cc082b17ff9d2e05d5fbdd0e60296d08','df64-product-carrier':'bf08c13264b7df9f6d350909bf4fbaee0ec152b327f508c9c971c80dedbc8e40','df64-next-re-carrier':'d6589040e2a74df6e07a87fde42351b2fd29cc93550947d1106b23f6d8c0fc4d','out-iteration':'30c8fb06d7d4f895e14cb9b022ff7c4192e3ca90fe8780cc4de9ffb8b2610d4e','out-z-magnitude2':'7ba3eacc7b9b8b8da2605660a467a5bce50d9e9b6e07c19454d550a2b66e8f66','out-derivative-magnitude2':'0aa48418f5c21ee957c609cdf0331624a843282cfb70eb70183de6d0870c9504','out-stripe-sum':'66392efe93e894248bac6c6bca7ae0d8f8549199289356b51b8ee66e1cfe7eb6','out-stripe-count':'d79ff37e0390f4091a72fe78876b0caa2f92347cf4eefff5bbbeca74a5b765fe','out-stripe-last':'69a85b0ccde99c3821f03dde06cb9e4ec3c94d7cbd1aae65306f3c75d6e65b4a','out-trap-min':'1a01779573462d720c6ae74e6bb10083ad6a9c3209ca508c262088f3903b1df2','transform-re-owner':'04cd174c201170ba87b4cc0f4c8e3a832aba6cff09ffcd6a884156ca9d4d627e','transform-im-owner':'7d323b5bac250bf655fecb32049b8754f5f65b9f5e2f2edac90caf7a993d2444','loop-bound':'d7827a7823840b51b49c31a86c8e2653bb2d14e2b28d599205c61f29ce05d461','period-loop-bound':'447482a148196100135bf5d27c8fa26cf758afd687b5207a377a0ae10395c3cd','log-smoothing':'d3bdfef870e6dc5fd8912686b44441d8441f6ad793f0caff514c9f46752e1f3a','log-distance':'b25f59f85a9fc1f67ab9871f119ece6223efe996d84d10e4713a050cd6f88b20','log-stripe':'a8ab022104954ba54031d07439b3370f16a0429130ef09ee0077c44782d3238d','log-stripe-normalization':'c9a5e600d8ac570b5a455d0abe636b41250288e4c2dd9e539de3d89cd310566f','normal-base':'ce8cafa48121a9466b05c1f0af84d75f2519ab4db210237cc85ac291fc403d76','normal-right':'ad0e24dfb436b1d9a353c9f662a29c736ff41e054eb09bd846ba6cc0576f264a','normal-up':'80ab37e7e4f95e706d4b5473d54d6704ec700dbc78e78462464dc3af644798fb'}
EXPECTED_REPLACEMENTS = {"cross-lane-dz-assignment":"60737b08ed7eb5909a883d8c0fba2abf6ffe477ffe7fc747d15e84e3de2cddd1","df64-re2-carrier":"7aff87de41586aa57188e9fadaed79afddb149412e1f898a9a2c2ba583b8f1eb","df64-im2-carrier":"f728fc3c75861ac1908f3c99d0ea01a573cd339d8690a2d89f4b082b48bff44d","df64-product-carrier":"76695fed4c1fa0e89f85bc1ca8703292489b39d3bf317152ee53cfc328a0fbce","df64-next-re-carrier":"3a1ab0e1e7a77817560db1257ff5e1d0a782e99ae4e0c09512501a932b87b84d","out-iteration":"7c4cfbe45467c7ae34c862d91ea3a57fca56ae082223347c90bebf83c421e206","out-z-magnitude2":"d36ed37ea88cc317e08d4c3ac1e323f95b964662c0462e1a851a0a3cf133a0e5","out-derivative-magnitude2":"4938e9681edd141d48686819c27b08698980e07efc1757c4e65917c5e470bec6","out-stripe-sum":"fd870248bb90468d89ea28efe5c0c9d53ecc29b04edcf28bc48e9de75de94471","out-stripe-count":"0f9d1fbd21929c819e18d9ac761c6492b874dfed91d452c17baf867baea78651","out-stripe-last":"e6b5d74c85d2c2ee381cb0302783776b2a008732775233d75d870d4a63f6ede5","out-trap-min":"5648290fd2fc4f963aed60553d5e08eb31bd05d7e9dc77c6853fcb4612e58ae9","transform-re-owner":"8826e0fbf5c6623a03a15cfe86306fa89e8ad1df362be765d151b390b26a0a51","transform-im-owner":"6b85f53f990d823afdd18bd215c236941a89c26d9b5be1365d8b57daad46bcfc","loop-bound":"848242238dd18b61ae89a14eebdf9ce4857f349e446cf4f62907e58e715f5c1f","period-loop-bound":"f65b14b1826bb113e75206d47e8644461c4cd4feeb9a24718d557a1b1134c16a","log-smoothing":"cd6ca2a350c60483ae4e939d5283d448a9c577b3d79d39454e7af1dfcd665603","log-distance":"23792fe1424127784d6fbbdcbf39cbb0929ed9248a0a75def3f46d265839f78d","log-stripe":"e25fa0a0c4a95a122b863167b47c6b43cd7c01ac8aa96371d8341a3a16c48500","log-stripe-normalization":"a73eaca2557ae94a9f8c1a9012d0f0a901df7f728417738a426d9604438f94a4","normal-base":"3e04065cbf9c389094b96442deb9efd72d584a8880ab25b33582377cc472db88","normal-right":"5ba5243c6744df3cc79bdf3c3c7c6a000cbb804e3d0936b9101fe3f7632ba490","normal-up":"59be8b2147353bae92cd1b09433f6d57c1bcd283d158fddf9a5eebff852ebe0e"}
EXPECTED_MUTATED = {"cross-lane-dz-assignment":"9fdd53914591d4bb4209094359c1450847beef8bf0426bf737c872de286d081e","df64-re2-carrier":"94c4d51c7c00b1ae740f57b0bc783c4d60a30aba5dc35312e3796069f16f4480","df64-im2-carrier":"5b81a2db3058cfab7595b182f445bfa32fa143279a8dc1ddf1e32f1416b54194","df64-product-carrier":"78904c52122d5ab142be1628ff4290dac7d143b529f4116dd4df4ad1927ad0fc","df64-next-re-carrier":"900bf690c575f4fdc517db041aac51ef59f78051ff257616e1750fe3dbbd1813","out-iteration":"c8f88c760fad861bfb6dbc4cd63f2f9a2c127daa35d2645e21418a8d8258ea3d","out-z-magnitude2":"69507160fcd2f53af070bd4db5c14749f09a7475339f72f498d5495993613427","out-derivative-magnitude2":"d836409e43fa5c3b1a222303b8a40dcba144eff89a813720ac5ee2773fe86541","out-stripe-sum":"c1e17b234f588162749c5a8766c48af04fd231af2ff24b7f439a580326fbbd33","out-stripe-count":"0bb332675454140bf47a02c53d47d18a8667500a0c6a642a616919b75c204a66","out-stripe-last":"bf00af11ec4f923f4c29890f8b53f55eaab6aaf36667dbd835513871fbf02018","out-trap-min":"0c18b2a9a2d2e2989e1bcc8f53ffbfb34606726710dc03b2f64d4358faef04aa","transform-re-owner":"e0db5ab13c82c1a50b6a2538bd97aaff2317d0f8a45345e21675abe6760d0e4b","transform-im-owner":"7d4ac5cb76054fa93bfa948bd867b32343ff171ab19d37308219c78db8156292","loop-bound":"dc56981c1d347992b9c390393acd073b9640afc653b476027230b2c437f8f4fb","period-loop-bound":"1fb47da10ab8baa42ee7fd469724eb7d282b8c37d8ec02ba767f23cbd47a5c5e","log-smoothing":"9937f3ecb41404f1c3f4a90763f31c75435c0baf0e88740eec6f539be5ccf0fc","log-distance":"e7b841834a4022189633c1374841a638b0e1c5dbc567059d0e3b7b84461fa50b","log-stripe":"c2da8e6fccffc9ae07940766e80c928d88e4641d7a6c23eae259d53c69c983f8","log-stripe-normalization":"328117479d486f509a70358ae46b8beda46b311f70084e0998f01c3d06f2d1a9","normal-base":"66c65e0b35b23b2d1f045ebc4b9526ff9f34c4ad8f387deddebbc142cec3ccb3","normal-right":"c124fce8fea05b2c9f75ce6d3e5f6c9bbe9aa1b2b1de4bdb79a11f98e4b3c8f9","normal-up":"32d90bc43c3c826cedfa0bb03c268b34e53babd03187fb3d826ca3a45bf75797"}
EXPECTED_RESULTS = {"cross-lane-dz-assignment":"c5b8beac982893ac64522366ea3e83f48ccfa24d73861f2c3417ca2b4a606139","df64-re2-carrier":"7730f38cbb99f500f18c8c37dcbba4d5c09a99842b63c2fbd6414e0ea20b3b20","df64-im2-carrier":"16629c129ba84103ad7790c3a9ccc8cdbe53ae4638d80f278cd3b3cff7923be4","df64-product-carrier":"d75b26cdd4c2f3f0cc88ed5165a7fa014393da336c95d3ffc671ef28c656867f","df64-next-re-carrier":"9026e868d28ca1ccbcc79960383b2be7f367bba319e08afc85db877243619229","out-iteration":"34d5fdbfa8a18d8242d50969aa2eafe721c8a101410ff5a647d9ea6f74da35ff","out-z-magnitude2":"255f94029b197ec43af4a06b7d329c48b39e642f02e4194ec5f5d69924228273","out-derivative-magnitude2":"819f9d48438cd31efe0aea1a246badc5d0b812d0534efcfb31fae10e31647a86","out-stripe-sum":"861fc9301f1fa66095da59968098574e7842196fc5393822beaffef40374442b","out-stripe-count":"001a1f1e39eaec265bf5ee6e66b35543fcdbd584bf38cbae97c349ceb7d4637e","out-stripe-last":"1a50c8857fb06f3bdf1749c4ce0cd72242150c6c451dc8880e39824b6fa48c23","out-trap-min":"b1c0186bd660bca72a0227208bd70a7309d3fd36b62e19d2f95fe5c26bbc712c","transform-re-owner":"4b37b8d75ecc2971defc168c7c9b2a51d1e982478c7fd464cc932612117d92ff","transform-im-owner":"eedc6dfa247a65fa7767ee45b21b490c2119945cebecb1b475101421204ad994","loop-bound":"7a5a4593b01cec110f891861977ec029fa521da2cd6698abe31c665fffe0c1dc","period-loop-bound":"737e2d5cb19a3df4aad23e15ec237c7f399824f1d63453b345ef009fd191c63a","log-smoothing":"e4e9a4d49c7e72e50079a38d3a0574eb48f9eea4dad2c691947b950f542f9679","log-distance":"7a148a283ba4544a4ea61a485f533decb73f378cd9d0f714dd5c6da675a42737","log-stripe":"f3a15acd12dac8cb281431fdfcd594fd5cb21f72862676b8a1f8751a944a31f7","log-stripe-normalization":"d2e37cee415b4e06403e54df9cae0efefc34da6f527e55eaf2c13ad644c2e65f","normal-base":"8eb7e4ade7e0d8037e7cbd85416eec95e6633a513818b984f49b77512619a0a1","normal-right":"a6caf6d6c53c01c205c7e4cf753ecb4de12abd9883a7b6533a17dd1d72bfa5af","normal-up":"7b4f68fdb7d1355925413c76277961d45ac3cfe0bfff403755680c274a86528e"}
EXPECTED_ANCHORS.update({'loop-clamp-1001':'d7827a7823840b51b49c31a86c8e2653bb2d14e2b28d599205c61f29ce05d461','result-trap-number':'0705f06f3f6101e0f7990e839bd1c4aef343ee08dc7bafccd654669843890eb3'})
EXPECTED_REPLACEMENTS.update({'loop-clamp-1001':'825df14610cc75d3e2a1e1e35276bce9686d82063e3d66f9c449100bc1e74f7b','result-trap-number':'68ec4220d8cf63fd98aa5a0c94a2ed59c776f3d5081c671ff1bc89f20eb1f358'})
EXPECTED_MUTATED.update({'loop-clamp-1001':'a5c1e3fe9530d06a8d6ccfaafd3f1b29c2221a35a7a874b6d48881281d9a9a18','result-trap-number':'abd2a68d17ebff2e2390ab0645e60f7a582dc1f42690228db9e3ae286939eda5'})
EXPECTED_RESULTS.update({'loop-clamp-1001':'0f88e75470219de768392d631715d11595f907434e966649335b739b2d785e71','result-trap-number':'9115e939e6b95fb0dc42683155c5d69bc2038d15090387c90be7c114e01dac73'})
EXPECTED_RESULTS.update({'cross-lane-dz-assignment':'4acdbcb21f93a80e55b86b5146a1de0ae96b576d7b23889e01fdca7f7bbd77cf','df64-re2-carrier':'801e1875f5d8bcaaed3c337c8d7446ef0f644f00c87152d8d7d88db017d8f364','df64-im2-carrier':'33e5e4ca77c5de1d4213eadaab863faf21024d1dc7e2b6b17564552bfb678576','df64-product-carrier':'7b5f2646cd6efbdc792bc4517f6a1c1cfca3204b70fdd9853c06f1f92f78baf6','df64-next-re-carrier':'6a82c920ece2f67d8b23e54c8bb14c28cc47f35d0a862d60f368f2163ee26c03','out-iteration':'da6dc9d91253a75b8d14246d1eaae27cf84939fcc6c4824cb5f196e7d3fbded4','out-z-magnitude2':'eac6aea4144444a3939d8b692dd1cc84e1a1303206037e3795ed69bdfc3b9e4e','out-derivative-magnitude2':'bda52bbbf81c7ae6324de92efa8ed6031d752b00bfadee8a72261d62e28ce8cf','out-stripe-sum':'29d37266e62062713a9f57016275b0d427adeb2171aed6ce08e70f0ff061a209','out-stripe-count':'42ab9d6e31b8f9b24a2c257d5564337d00b3e0f89ae62ed5d1eb5c5a2f8c65b7','out-stripe-last':'399c49689696fbb38060af8b5ca33c2f50c9f595a6df829859ff49013d22a5b3','out-trap-min':'cd07570d3ff8f4ac4459d9f21adb7fc142d1b3556559c8dc4a09d02a26483047','transform-re-owner':'c19195e92293ce1ac789b98e76a6b147de048ae25f8a8ab1e1de9432d6807bbf','transform-im-owner':'4e4155930e7e5e0eabca37afadba4ca4fb9979cfc5b5ca915782be454055f949','loop-bound':'3516a069429ec40e22eb461bab3a693e2269253b2a52992711895303de9d07ae','period-loop-bound':'c473345c2346fabec474799beb06fba0bb6e9bdc19ad00dcc24ac6c1a8f62411','log-smoothing':'950d307ecd1dc902ae3be8a05c2813d726c4c93970c0a349ab1b97d811552778','log-distance':'d7c742fe96564afc28cb5d863d1b24119c0ef8ae4ed0e60feca4fe2e9cfe918c','log-stripe':'fa98057c765a6f6901336ba44627a27efab51397e85fc694cc608c2e677a0292','log-stripe-normalization':'b0088d0eaaf30bcc4f15841d75b8e3b4abcd1b540dc177a68d041ea155df9eab','normal-base':'76c6354657e987109a97770fc09dc4b0fe9bcf14f3a8539d56b19752367c713c','normal-right':'99438a9a181e430315aa124e2d87638739d8e7bf46ef1b65cc2f5f6ccfdebb8c','normal-up':'9bd4ee9f88cf66a806c078d65609fe631d35d6a606f99607cf9a4f11fed74885'})
EXPECTED_RESULTS = {'cross-lane-dz-assignment':'4acdbcb21f93a80e55b86b5146a1de0ae96b576d7b23889e01fdca7f7bbd77cf','df64-re2-carrier':'15a47a2e97e32935c2851c33c16a79f73bfffcf07570f8b571e865b756f82ae2','df64-im2-carrier':'6df249c1c71abb6262030b8425d4d37628c629dc7fc44ff38aa7f6a6b5f3bad7','df64-product-carrier':'77da401b37b415f8286e8599265f3035a8d9ded0091b0c1e1cf0348121270afa','df64-next-re-carrier':'3251bfa71d38c3b48b52ec497f7ef4c4bf1335ba79cfc880058ffa1cb41de247','out-iteration':'f50656a389d4bbd9370f9d19a61822df479dfe125386d8b083e34cdd2b90bc1d','out-z-magnitude2':'e9ec50a9e509fa3847ba149892528d5320aa08418a98fa566e697f3badde58a9','out-derivative-magnitude2':'bda52bbbf81c7ae6324de92efa8ed6031d752b00bfadee8a72261d62e28ce8cf','out-stripe-sum':'29d37266e62062713a9f57016275b0d427adeb2171aed6ce08e70f0ff061a209','out-stripe-count':'42ab9d6e31b8f9b24a2c257d5564337d00b3e0f89ae62ed5d1eb5c5a2f8c65b7','out-stripe-last':'399c49689696fbb38060af8b5ca33c2f50c9f595a6df829859ff49013d22a5b3','out-trap-min':'52e45382437e15a0004b2c25fea5b1dcbb522ec8f08c15ef10be2dfd85fc5997','transform-re-owner':'e99ceaec06045d872d591a097cac99c40fd34aab391271c90bb029d1456bbdc6','transform-im-owner':'f7af78218f8f7d1f4b3e71f2970da9c6bbe5d1487fb2a716dce795a9ec5924f3','loop-bound':'b7e2fad5e0b22d15dac9c45cb2e259aca69928363111918be8aefb5348634e18','loop-clamp-1001':'8d2097f509bb15eb75a1f3d7e4c184ef8a55d303c1c80585eec4cec8b2fcb796','period-loop-bound':'ea095a58e3b6d5df72611ca9dfbd20f602979362bf390b78da3cc5fb8b6c82a2','log-smoothing':'ed124e272782a8e08152fca66b52c5c26e42310cd1e384244392c2edaf247086','log-distance':'d7c742fe96564afc28cb5d863d1b24119c0ef8ae4ed0e60feca4fe2e9cfe918c','log-stripe':'fa98057c765a6f6901336ba44627a27efab51397e85fc694cc608c2e677a0292','log-stripe-normalization':'b0088d0eaaf30bcc4f15841d75b8e3b4abcd1b540dc177a68d041ea155df9eab','normal-base':'8520a894a1cdd89832fb2750eb673c9c9ca354e64137ab7b2f98953a1bc5e565','normal-right':'fa3cb216ac0941e39827719196c4166658bd8c6cf4cb1db3e5d3143f2296925c','normal-up':'59e3cfc76f8f46b63c0d269912d1b036d0fa0bb062ace36dd7a46e450954a058','result-trap-number':'9115e939e6b95fb0dc42683155c5d69bc2038d15090387c90be7c114e01dac73'}
EXPECTED_FORGE_CHECKS = 65
DIAGNOSTIC_ANCHOR_SHA = "fc8f0c37a014b2f996687589bf96d3fd9a70c2d82392e90d27b91ffdd03d71dc"
DIAGNOSTIC_REPLACEMENT_SHA = "4b07de3f6020508a97bd3a436a1d6111651703fcbc4a75010b281e4895171f12"
DIAGNOSTIC_FACTORY_SHA = "e64f2eadd238f437ed23f0812e35b8b145fbb8c96f4fa3cd38c19adde16bf40c"
EXPECTED_TRAP_SEARCH_BINDING = {
    "name": "trap-search-152217", "width": 1, "height": 1,
    "time": 3.7923567490168746, "cReal": -0.3738171601141377,
    "cImag": 0.4634542822519909, "poi": 6, "outputMode": 3,
    "centerX": 0.44228784680419775, "centerY": -0.3502212589025081,
    "rotation": 77.56369656360795, "iterations": 992, "stripeFreq": 0,
    "trapShape": 0, "lightAngle": 237.31254449982956, "cPath": 0,
    "cSpeed": 1.9575383979728302, "cRadius": 0.13296835996046857,
    "invert": False, "zoomSpeed": 0, "zoomDepth": 4.020128862238519,
    "tileX": 0, "tileY": 0, "salt": 1,
}
EXPECTED_TRAP_SEARCH_CANONICAL_F32 = ["0x3f3d3d3d", "0x3f3d3d3d", "0x3f3d3d3d", "0x3f800000"]
EXPECTED_TRAP_SEARCH_MUTATED_F32 = ["0x3f3d3d3e", "0x3f3d3d3e", "0x3f3d3d3e", "0x3f800000"]
EXPECTED_TRAP_SEARCH_CANONICAL_RGBA8 = [188, 188, 188, 255]
EXPECTED_TRAP_SEARCH_MUTATED_RGBA8 = [189, 189, 189, 255]

class MaterializationError(RuntimeError):
    pass

def strict_json(payload):
    def pairs(items):
        result = {}
        for key, value in items:
            if key in result:
                raise MaterializationError(f"duplicate JSON key: {key}")
            result[key] = value
        return result
    try:
        return json.loads(payload, object_pairs_hook=pairs)
    except MaterializationError:
        raise
    except json.JSONDecodeError as exc:
        raise MaterializationError(f"invalid JSON: {exc}") from exc

HEX_WORD = re.compile(r"^0x[0-9a-f]{8}$")
TOP_FIELDS = {"schema","schema_version","program_key","effect_key","runtime_key","corpus_revision","upstream_revision","factory","runtime_binding_names","runtime_binding_abi","source_uniform_abi","canonical_binding_contract","exactness_contract","comparer_self_tests","provenance","render_cases","source_mutation_contract","mutation_anchor_cardinality","mutation_ledger","control_group","cross_lane_assignment_profile","claim_boundaries","relations","diagnostic_witnesses","result_trap_search"}
CASE_FIELDS = {"name","width","height","time","cReal","cImag","poi","outputMode","centerX","centerY","rotation","iterations","stripeFreq","trapShape","lightAngle","cPath","cSpeed","cRadius","invert","zoomSpeed","zoomDepth","tileX","tileY","salt","input","expected","alpha_f32_word","alpha_rgba8_byte","input_immutable_exact_bits","bindings"}
INPUT_FIELDS = {"width","height","f32_words_le","f32_sha256"}
EXPECTED_FIELDS = {"f32_words_le","f32_sha256","rgba8_bytes","rgba8_sha256"}
MUTATION_FIELDS = {"name","group","mechanism","anchor","replacement","independent","source_anchor","anchor_occurrence_count","source_relative_path","source_sha256","canonical_factory_text_sha256","mutated_factory_text_sha256","anchor_sha256","replacement_sha256","results","result_sha256","witness_cases","control_cases"}
RESULT_TRAP_SOURCE_SPAN = "julia.js:158:7-47"

def exact(value, keys, label):
    if not isinstance(value, dict) or set(value) != set(keys):
        raise MaterializationError(f"{label}: exact field set")

def _require_string(value, label):
    if type(value) is not str:
        raise MaterializationError(f"{label}: expected string")

def _require_bool(value, label):
    if type(value) is not bool:
        raise MaterializationError(f"{label}: expected bool")

def _require_int(value, label):
    if type(value) is not int:
        raise MaterializationError(f"{label}: expected exact int")

def _require_number(value, label):
    if type(value) not in (int, float):
        raise MaterializationError(f"{label}: expected finite number")
    try:
        converted = float(value)
    except (OverflowError, ValueError) as exc:
        raise MaterializationError(f"{label}: expected finite number") from exc
    if not math.isfinite(converted):
        raise MaterializationError(f"{label}: expected finite number")

def _require_strings(values, label):
    if not isinstance(values, list) or any(type(value) is not str for value in values):
        raise MaterializationError(f"{label}: expected string list")

def _require_string_map(value, label):
    if not isinstance(value, dict) or any(type(key) is not str or type(child) is not str for key, child in value.items()):
        raise MaterializationError(f"{label}: expected string map")

def _require_number_list(values, count, label):
    if not isinstance(values, list) or len(values) != count:
        raise MaterializationError(f"{label}: expected {count} values")
    for index, value in enumerate(values):
        _require_number(value, f"{label}[{index}]")

def _require_hex(value, label):
    if type(value) is not str or not re.fullmatch(r"[0-9a-f]{64}", value):
        raise MaterializationError(f"{label}: expected lowercase SHA-256")

def _validate_scalar_types(doc):
    for field in ("schema", "program_key", "effect_key", "runtime_key", "corpus_revision", "upstream_revision"):
        _require_string(doc[field], field)
    _require_int(doc["schema_version"], "schema_version")
    exact(doc["factory"], {"name", "text_sha256", "public_factory_is_canonical_identity", "adapter_own_key"}, "factory types")
    _require_string(doc["factory"]["name"], "factory.name")
    _require_hex(doc["factory"]["text_sha256"], "factory.text_sha256")
    _require_bool(doc["factory"]["public_factory_is_canonical_identity"], "factory.public_factory_is_canonical_identity")
    _require_bool(doc["factory"]["adapter_own_key"], "factory.adapter_own_key")
    _require_strings(doc["runtime_binding_names"], "runtime_binding_names")
    _require_string_map(doc["runtime_binding_abi"], "runtime_binding_abi")
    _require_string_map(doc["source_uniform_abi"], "source_uniform_abi")
    exact(doc["canonical_binding_contract"], {"names", "abi", "source_abi"}, "canonical binding types")
    _require_strings(doc["canonical_binding_contract"]["names"], "canonical_binding_contract.names")
    _require_string_map(doc["canonical_binding_contract"]["abi"], "canonical_binding_contract.abi")
    _require_string_map(doc["canonical_binding_contract"]["source_abi"], "canonical_binding_contract.source_abi")
    _require_string_map(doc["exactness_contract"], "exactness_contract")
    exact(doc["comparer_self_tests"], {"dimensions_before_access", "first_mismatch_reported", "raw_words_and_rgba8_independent", "cases"}, "comparer self-tests")
    for field in ("dimensions_before_access", "first_mismatch_reported", "raw_words_and_rgba8_independent"):
        _require_bool(doc["comparer_self_tests"][field], f"comparer_self_tests.{field}")
    exact(doc["comparer_self_tests"]["cases"], {"good", "dimensions", "short", "long", "rgba8_count", "rgba8_mismatch", "signed_zero", "nan_payload"}, "comparer cases")
    for field, value in doc["comparer_self_tests"]["cases"].items():
        _require_bool(value, f"comparer_self_tests.cases.{field}")
    prov = doc["provenance"]
    exact(prov, {"source", "factory_source", "cpu_snapshot", "generator", "materializer"}, "provenance types")
    for field in ("source", "factory_source"):
        exact(prov[field], {"relative_path", "sha256"}, f"provenance.{field} types")
        _require_string(prov[field]["relative_path"], f"provenance.{field}.relative_path")
        _require_hex(prov[field]["sha256"], f"provenance.{field}.sha256")
    snap = prov["cpu_snapshot"]
    exact(snap, {"argument", "immutable_snapshot", "realpath_containment_checked", "live_checkout_rejected", "import_closure"}, "cpu_snapshot types")
    _require_string(snap["argument"], "cpu_snapshot.argument")
    for field in ("immutable_snapshot", "realpath_containment_checked", "live_checkout_rejected"):
        _require_bool(snap[field], f"cpu_snapshot.{field}")
    if not isinstance(snap["import_closure"], list):
        raise MaterializationError("cpu_snapshot.import_closure: expected list")
    for index, entry in enumerate(snap["import_closure"]):
        exact(entry, {"relative_path", "sha256"}, f"import_closure[{index}] types")
        _require_string(entry["relative_path"], f"import_closure[{index}].relative_path")
        _require_hex(entry["sha256"], f"import_closure[{index}].sha256")
    for field in ("generator", "materializer"):
        exact(prov[field], {"relative_path", "sha256"}, f"provenance.{field} types")
        _require_string(prov[field]["relative_path"], f"provenance.{field}.relative_path")
        _require_hex(prov[field]["sha256"], f"provenance.{field}.sha256")
    if not isinstance(doc["render_cases"], list):
        raise MaterializationError("render_cases: expected list")
    integer_case_fields = ("width", "height", "poi", "outputMode", "iterations", "trapShape", "cPath", "salt")
    number_case_fields = ("time", "cReal", "cImag", "centerX", "centerY", "rotation", "stripeFreq", "lightAngle", "cSpeed", "cRadius", "zoomSpeed", "zoomDepth", "tileX", "tileY")
    for index, case in enumerate(doc["render_cases"]):
        label = f"case {index}"
        exact(case, CASE_FIELDS, f"{label} types")
        _require_string(case["name"], f"{label}.name")
        for field in integer_case_fields:
            _require_int(case[field], f"{label}.{field}")
        for field in number_case_fields:
            _require_number(case[field], f"{label}.{field}")
        _require_bool(case["invert"], f"{label}.invert")
        _require_string(case["alpha_f32_word"], f"{label}.alpha_f32_word")
        _require_int(case["alpha_rgba8_byte"], f"{label}.alpha_rgba8_byte")
        _require_bool(case["input_immutable_exact_bits"], f"{label}.input_immutable_exact_bits")
        exact(case["bindings"], set(EXPECTED_NAMES), f"{label}.bindings types")
        for field in ("resolution", "tileOffset", "fullResolution"):
            _require_number_list(case["bindings"][field], 2, f"{label}.bindings.{field}")
        for field in EXPECTED_NAMES[3:]:
            kind = EXPECTED_ABI[field]
            if kind == "int32":
                _require_int(case["bindings"][field], f"{label}.bindings.{field}")
            elif kind == "bool":
                _require_bool(case["bindings"][field], f"{label}.bindings.{field}")
            else:
                _require_number(case["bindings"][field], f"{label}.bindings.{field}")
        exact(case["input"], INPUT_FIELDS, f"{label}.input types")
        _require_int(case["input"]["width"], f"{label}.input.width")
        _require_int(case["input"]["height"], f"{label}.input.height")
        _require_hex(case["input"]["f32_sha256"], f"{label}.input.f32_sha256")
        exact(case["expected"], EXPECTED_FIELDS, f"{label}.expected types")
        _require_hex(case["expected"]["f32_sha256"], f"{label}.expected.f32_sha256")
        _require_hex(case["expected"]["rgba8_sha256"], f"{label}.expected.rgba8_sha256")
        if not isinstance(case["expected"]["rgba8_bytes"], list):
            raise MaterializationError(f"{label}.expected.rgba8_bytes: expected list")
        for byte_index, byte in enumerate(case["expected"]["rgba8_bytes"]):
            _require_int(byte, f"{label}.expected.rgba8_bytes[{byte_index}]")
    diagnostics = doc["diagnostic_witnesses"]
    if not isinstance(diagnostics, list) or len(diagnostics) != 1: raise MaterializationError("diagnostic witness cardinality")
    diagnostic = diagnostics[0]
    exact(diagnostic, {"name","source_anchor","replacement","anchor_occurrence_count","anchor_sha256","replacement_sha256","canonical_factory_text_sha256","instrumented_factory_text_sha256","period_hit_count","canonical","instrumented"}, "diagnostic witness")
    if diagnostic["name"] != "period-convergence" or diagnostic["anchor_occurrence_count"] != 1 or diagnostic["period_hit_count"] < 1: raise MaterializationError("diagnostic witness identity")
    if diagnostic["anchor_sha256"] != DIAGNOSTIC_ANCHOR_SHA or diagnostic["replacement_sha256"] != DIAGNOSTIC_REPLACEMENT_SHA or diagnostic["instrumented_factory_text_sha256"] != DIAGNOSTIC_FACTORY_SHA or diagnostic["canonical_factory_text_sha256"] != FACTORY_SHA: raise MaterializationError("diagnostic source hashes")
    for label, output in (("canonical", diagnostic["canonical"]),("instrumented", diagnostic["instrumented"])):
        exact(output, {"f32_words_le","rgba8_bytes"}, f"diagnostic {label}")
        words(output["f32_words_le"], 4, f"diagnostic {label} words")
        if not isinstance(output["rgba8_bytes"], list) or len(output["rgba8_bytes"]) != 4 or any(type(byte) is not int or not 0 <= byte <= 255 for byte in output["rgba8_bytes"]): raise MaterializationError(f"diagnostic {label} bytes")
    if diagnostic["canonical"] != diagnostic["instrumented"]: raise MaterializationError("diagnostic output drift")
    search = doc["result_trap_search"]
    exact(search, {"selection_rule", "tested_candidates", "limit", "selected"}, "result trap search")
    _require_string(search["selection_rule"], "result_trap_search.selection_rule")
    _require_int(search["tested_candidates"], "result_trap_search.tested_candidates")
    _require_int(search["limit"], "result_trap_search.limit")
    if search["tested_candidates"] != 152236 or search["limit"] != 200000 or search["selection_rule"] != "poi-trap-first, then trap-search-000000 through trap-search-199999": raise MaterializationError("result trap search contract")
    selected = search["selected"]
    exact(selected, {"order_index", "binding", "canonical", "mutated", "changed_float32_lanes", "changed_rgba8_bytes", "float32_witness", "rgba8_witness"}, "result trap search selected")
    _require_int(selected["order_index"], "result_trap_search.selected.order_index")
    _require_int(selected["changed_float32_lanes"], "result_trap_search.selected.changed_float32_lanes")
    _require_int(selected["changed_rgba8_bytes"], "result_trap_search.selected.changed_rgba8_bytes")
    if selected["order_index"] < 0 or selected["changed_float32_lanes"] < 1 or selected["changed_rgba8_bytes"] < 1: raise MaterializationError("result trap search witness counts")
    exact(selected["binding"], set(CASE_FIELDS) - {"input", "expected", "alpha_f32_word", "alpha_rgba8_byte", "input_immutable_exact_bits", "bindings"}, "result trap search binding")
    _require_string(selected["binding"]["name"], "result_trap_search.selected.binding.name")
    if selected["order_index"] != 152235 or selected["changed_float32_lanes"] != 3 or selected["changed_rgba8_bytes"] != 3 or selected["binding"] != EXPECTED_TRAP_SEARCH_BINDING: raise MaterializationError("result trap search selected binding")
    exact(selected["canonical"], {"f32_words_le", "rgba8_bytes"}, "result trap search canonical")
    exact(selected["mutated"], {"f32_words_le", "rgba8_bytes"}, "result trap search mutated")
    words(selected["canonical"]["f32_words_le"], 4, "result trap search canonical words")
    words(selected["mutated"]["f32_words_le"], 4, "result trap search mutated words")
    for label in ("canonical", "mutated"):
        if not isinstance(selected[label]["rgba8_bytes"], list) or len(selected[label]["rgba8_bytes"]) != 4 or any(type(byte) is not int or not 0 <= byte <= 255 for byte in selected[label]["rgba8_bytes"]): raise MaterializationError(f"result trap search {label} bytes")
    if selected["canonical"]["f32_words_le"] != EXPECTED_TRAP_SEARCH_CANONICAL_F32 or selected["mutated"]["f32_words_le"] != EXPECTED_TRAP_SEARCH_MUTATED_F32 or selected["canonical"]["rgba8_bytes"] != EXPECTED_TRAP_SEARCH_CANONICAL_RGBA8 or selected["mutated"]["rgba8_bytes"] != EXPECTED_TRAP_SEARCH_MUTATED_RGBA8: raise MaterializationError("result trap search selected pixels")
    for field, expected_kind in (("float32_witness", "string"), ("rgba8_witness", "int")):
        witness = selected[field]
        exact(witness, {"index", "expected", "actual"}, f"result trap search {field}")
        _require_int(witness["index"], f"result trap search {field}.index")
        if expected_kind == "string":
            if not HEX_WORD.fullmatch(witness["expected"]) or not HEX_WORD.fullmatch(witness["actual"]): raise MaterializationError(f"result trap search {field} words")
        else:
            if any(type(witness[key]) is not int or not 0 <= witness[key] <= 255 for key in ("expected", "actual")): raise MaterializationError(f"result trap search {field} bytes")
        if witness["expected"] == witness["actual"]: raise MaterializationError(f"result trap search {field} is not discriminating")
    relations = doc["relations"]
    exact(relations, {"clamp_1001_vs_1000","fallbacks"}, "relations")
    clamp = relations["clamp_1001_vs_1000"]
    exact(clamp, {"name","kind","candidate_case","control_case","identical_float32","identical_rgba8","mutant_name","mutant_candidate_changed_float32_lanes","mutant_candidate_changed_rgba8_bytes","mutant_control_changed_float32_lanes","mutant_control_changed_rgba8_bytes","source_anchor","instrumentation","mutant_replacement","loop_anchor_occurrence_count","loop_anchor_sha256","instrumentation_sha256","mutant_factory_text_sha256","case","canonical_1000_loop_entries","canonical_1001_loop_entries","no_clamp_mutant_loop_entries","instrumented_canonical_1000_pixel_identical","instrumented_canonical_1001_pixel_identical","instrumented_mutant_pixel_identical","canonical_1000","canonical_1001","canonical_1000_vs_1001_identical_float32","canonical_1000_vs_1001_identical_rgba8","mutant_candidate_first_float32_witness","mutant_candidate_first_rgba8_witness"}, "clamp relation")
    if clamp["name"] != "iterations-clamp-1001-vs-1000" or clamp["kind"] != "runtime-loop-clamp-observation" or clamp["candidate_case"] != "iterations-clamp-1001" or clamp["control_case"] != "iterations-max" or clamp["mutant_name"] != "loop-clamp-1001" or clamp["mutant_candidate_changed_float32_lanes"] < 1 or clamp["mutant_candidate_changed_rgba8_bytes"] < 1 or clamp["loop_anchor_occurrence_count"] != 1 or clamp["source_anchor"] != "for (let index = 0; index < Math.min(maxIterations, 1000); index += 1) {" or clamp["mutant_replacement"] != "maxIterations" or clamp["case"] != "iterations-clamp-1001" or clamp["canonical_1000_loop_entries"] != 1000 or clamp["canonical_1001_loop_entries"] != 1000 or clamp["no_clamp_mutant_loop_entries"] != 1001 or any(clamp[field] is not True for field in ("instrumented_canonical_1000_pixel_identical", "instrumented_canonical_1001_pixel_identical", "instrumented_mutant_pixel_identical")): raise MaterializationError("clamp relation contract")
    for label in ("canonical_1000", "canonical_1001"):
        exact(clamp[label], {"f32_words_le", "rgba8_bytes"}, f"clamp {label}")
        words(clamp[label]["f32_words_le"], 4, f"clamp {label} words")
        if not isinstance(clamp[label]["rgba8_bytes"], list) or len(clamp[label]["rgba8_bytes"]) != 4 or any(type(byte) is not int or not 0 <= byte <= 255 for byte in clamp[label]["rgba8_bytes"]): raise MaterializationError(f"clamp {label} bytes")
    if not isinstance(clamp["identical_float32"], bool) or not isinstance(clamp["identical_rgba8"], bool): raise MaterializationError("clamp canonical relation types")
    if not isinstance(relations["fallbacks"], list) or len(relations["fallbacks"]) != 3: raise MaterializationError("fallback relation cardinality")
    for fallback in relations["fallbacks"]:
        exact(fallback, {"name","kind","candidate_case","canonical_control","identical_float32","identical_rgba8","candidate","control"}, "fallback relation")
        if fallback["identical_float32"] is not True or fallback["identical_rgba8"] is not True: raise MaterializationError("fallback relation equality")
        for label in ("candidate","control"):
            exact(fallback[label], {"f32_words_le","rgba8_bytes"}, f"fallback {label}")
            if not isinstance(fallback[label]["f32_words_le"], list) or not isinstance(fallback[label]["rgba8_bytes"], list): raise MaterializationError("fallback output arrays")
    exact(doc["source_mutation_contract"], {"source_relative_path", "source_sha256", "shader_relative_path", "shader_sha256", "canonical_factory_text_sha256", "execution"}, "source mutation contract types")
    _require_string_map(doc["source_mutation_contract"], "source_mutation_contract")
    exact(doc["mutation_anchor_cardinality"], {"total", "by_group", "anchors"}, "mutation cardinality types")
    _require_int(doc["mutation_anchor_cardinality"]["total"], "mutation_anchor_cardinality.total")
    for field in ("by_group", "anchors"):
        value = doc["mutation_anchor_cardinality"][field]
        if not isinstance(value, dict):
            raise MaterializationError(f"mutation_anchor_cardinality.{field}: expected map")
        for key, count in value.items():
            _require_string(key, f"mutation_anchor_cardinality.{field} key")
            _require_int(count, f"mutation_anchor_cardinality.{field}.{key}")
    if not isinstance(doc["mutation_ledger"], list):
        raise MaterializationError("mutation_ledger: expected list")
    for mutation_index, mutation in enumerate(doc["mutation_ledger"]):
        label = f"mutation {mutation_index}"
        mutation_fields = MUTATION_FIELDS | ({"source_span"} if mutation.get("name") == "result-trap-number" else set())
        exact(mutation, mutation_fields, f"{label} types")
        for field in ("name", "group", "mechanism", "anchor", "replacement", "source_anchor", "source_relative_path", "source_sha256", "canonical_factory_text_sha256", "mutated_factory_text_sha256", "anchor_sha256", "replacement_sha256", "result_sha256"):
            _require_string(mutation[field], f"{label}.{field}")
        _require_bool(mutation["independent"], f"{label}.independent")
        _require_int(mutation["anchor_occurrence_count"], f"{label}.anchor_occurrence_count")
        if not isinstance(mutation["witness_cases"], list) or not isinstance(mutation["control_cases"], list):
            raise MaterializationError(f"{label}: witness/control lists")
        _require_strings(mutation["witness_cases"], f"{label}.witness_cases")
        _require_strings(mutation["control_cases"], f"{label}.control_cases")
        if not isinstance(mutation["results"], list):
            raise MaterializationError(f"{label}.results: expected list")
        for result_index, row in enumerate(mutation["results"]):
            row_label = f"{label}.results[{result_index}]"
            exact(row, {"case", "differs", "changed_float32_lanes", "changed_rgba8_bytes", "float32_witness", "rgba8_witness"}, f"{row_label} types")
            _require_string(row["case"], f"{row_label}.case")
            _require_bool(row["differs"], f"{row_label}.differs")
            _require_int(row["changed_float32_lanes"], f"{row_label}.changed_float32_lanes")
            _require_int(row["changed_rgba8_bytes"], f"{row_label}.changed_rgba8_bytes")
            for field, expected_kind in (("float32_witness", "string"), ("rgba8_witness", "int")):
                witness = row[field]
                if witness is None:
                    continue
                exact(witness, {"index", "expected", "actual"}, f"{row_label}.{field}")
                _require_int(witness["index"], f"{row_label}.{field}.index")
                if expected_kind == "string":
                    _require_string(witness["expected"], f"{row_label}.{field}.expected")
                    _require_string(witness["actual"], f"{row_label}.{field}.actual")
                else:
                    _require_int(witness["expected"], f"{row_label}.{field}.expected")
                    _require_int(witness["actual"], f"{row_label}.{field}.actual")
    exact(doc["control_group"], {"repeatability", "input_immutability", "input_lifetime", "independent_output_storage", "public_direct_identity", "adapter_own_key"}, "control group types")
    for field in ("public_direct_identity", "adapter_own_key"):
        _require_bool(doc["control_group"][field], f"control_group.{field}")
    for group in ("repeatability", "input_immutability", "input_lifetime", "independent_output_storage"):
        _require_string(doc["control_group"][group]["case"], f"control_group.{group}.case")
        for key, value in doc["control_group"][group].items():
            if key != "case":
                _require_bool(value, f"control_group.{group}.{key}")
    exact(doc["cross_lane_assignment_profile"], {"status", "contract", "source_bound", "anchor", "replacement", "mutated_factory_text_sha256"}, "cross-lane profile types")
    _require_string_map(doc["cross_lane_assignment_profile"], "cross_lane_assignment_profile")
    _require_string_map(doc["claim_boundaries"], "claim_boundaries")

def reject_absolute(value, label="document"):
    if isinstance(value, str):
        if value.startswith("/") or re.match(r"^[A-Za-z]:[\\/]", value) or value.startswith("file:"):
            raise MaterializationError(f"{label}: absolute path")
    elif isinstance(value, dict):
        for key, child in value.items(): reject_absolute(child, f"{label}.{key}")
    elif isinstance(value, list):
        for index, child in enumerate(value): reject_absolute(child, f"{label}[{index}]")

def _pack(words_value):
    import struct
    try:
        return b"".join(struct.pack("<I", int(word, 16)) for word in words_value)
    except (TypeError, ValueError, struct.error) as exc:
        raise MaterializationError("invalid Float32 word") from exc

def words(value, count, label):
    if not isinstance(value, list) or len(value) != count or any(not isinstance(word, str) or not HEX_WORD.fullmatch(word) for word in value):
        raise MaterializationError(f"{label}: exact Float32 word count/format")
    return value

def _fixed_case(case):
    return {key: value for key, value in case.items() if not key.endswith("_sha256") and key not in {"input", "expected"}}

def _expected_binding(case):
    return {"resolution":[case["width"],case["height"]],"tileOffset":[case["tileX"],case["tileY"]],"fullResolution":[case["width"],case["height"]],**{name:case[name] for name in EXPECTED_NAMES[3:]}}

def compare_exact(expected, actual):
    if not isinstance(expected, dict) or not isinstance(actual, dict): raise MaterializationError("comparer: document shape")
    for key in ("width", "height"):
        if actual.get(key) != expected.get(key): raise MaterializationError(f"comparer: dimension mismatch at {key}")
    count = expected["width"] * expected["height"] * 4
    ew, aw = expected.get("f32_words_le"), actual.get("f32_words_le")
    if not isinstance(aw, list) or len(aw) != count: raise MaterializationError("comparer: Float32 count mismatch")
    if not isinstance(ew, list) or len(ew) != count: raise MaterializationError("comparer: expected Float32 count mismatch")
    for index, (left, right) in enumerate(zip(ew, aw)):
        if left != right: raise MaterializationError(f"comparer: Float32 mismatch at {index}: {left} != {right}")
    eb, ab = expected.get("rgba8_bytes"), actual.get("rgba8_bytes")
    if not isinstance(ab, list) or len(ab) != count: raise MaterializationError("comparer: RGBA8 count mismatch")
    if not isinstance(eb, list) or len(eb) != count: raise MaterializationError("comparer: expected RGBA8 count mismatch")
    for index, (left, right) in enumerate(zip(eb, ab)):
        if left != right: raise MaterializationError(f"comparer: RGBA8 mismatch at {index}: {left} != {right}")
    return True

def validate(doc):
    if not isinstance(doc, dict): raise MaterializationError("document must be an object")
    exact(doc, TOP_FIELDS, "top-level")
    _validate_scalar_types(doc)
    reject_absolute(doc)
    if doc["schema"] != SCHEMA or doc["schema_version"] != 1 or doc["program_key"] != KEY or doc["effect_key"] != "synth/julia" or doc["runtime_key"] != KEY or doc["corpus_revision"] != CORPUS or doc["upstream_revision"] != UPSTREAM: raise MaterializationError("identity/schema contract")
    if doc["runtime_binding_names"] != EXPECTED_NAMES or doc["runtime_binding_abi"] != EXPECTED_ABI or doc["source_uniform_abi"] != EXPECTED_SOURCE_ABI: raise MaterializationError("binding/source ABI contract")
    exact(doc["factory"], {"name","text_sha256","public_factory_is_canonical_identity","adapter_own_key"}, "factory")
    if doc["factory"] != {"name":"juliaFactory","text_sha256":FACTORY_SHA,"public_factory_is_canonical_identity":True,"adapter_own_key":True}: raise MaterializationError("factory identity contract")
    if doc["canonical_binding_contract"] != {"names":EXPECTED_NAMES,"abi":EXPECTED_ABI,"source_abi":EXPECTED_SOURCE_ABI}: raise MaterializationError("canonical binding contract")
    if doc["exactness_contract"] != EXACTNESS or doc["comparer_self_tests"] != COMPARER: raise MaterializationError("exactness/comparer contract")
    prov = doc["provenance"]
    exact(prov, {"source","factory_source","cpu_snapshot","generator","materializer"}, "provenance")
    exact(prov["source"], {"relative_path","sha256"}, "source provenance")
    exact(prov["factory_source"], {"relative_path","sha256"}, "factory provenance")
    if prov["source"] != {"relative_path":SOURCE,"sha256":SOURCE_SHA} or prov["factory_source"] != {"relative_path":FACTORY_SOURCE,"sha256":FACTORY_SOURCE_SHA}: raise MaterializationError("source provenance contract")
    snap = prov["cpu_snapshot"]
    exact(snap, {"argument","immutable_snapshot","realpath_containment_checked","live_checkout_rejected","import_closure"}, "cpu snapshot")
    if snap["argument"] != "<immutable-cpu-snapshot-root>" or any(snap[key] is not True for key in ("immutable_snapshot","realpath_containment_checked","live_checkout_rejected")): raise MaterializationError("cpu snapshot contract")
    closure = snap["import_closure"]
    if not isinstance(closure, list) or len(closure) != len(EXPECTED_CLOSURE): raise MaterializationError("import closure cardinality")
    for entry in closure:
        exact(entry, {"relative_path","sha256"}, "import closure entry")
        if entry["relative_path"].startswith("/") or not re.fullmatch(r"[0-9a-f]{64}", entry["sha256"]): raise MaterializationError("import closure entry format")
    if {entry["relative_path"]:entry["sha256"] for entry in closure} != EXPECTED_CLOSURE or len({entry["relative_path"] for entry in closure}) != len(closure): raise MaterializationError("import closure hash/path contract")
    exact(prov["generator"], {"relative_path","sha256"}, "generator provenance")
    exact(prov["materializer"], {"relative_path","sha256"}, "materializer provenance")
    if prov["generator"] != {"relative_path":GENERATOR_RELATIVE,"sha256":GENERATOR_SHA} or prov["materializer"] != {"relative_path":MATERIALIZER_RELATIVE,"sha256":hashlib.sha256(pathlib.Path(__file__).read_bytes()).hexdigest()}: raise MaterializationError("tool provenance contract")
    cases = doc["render_cases"]
    if not isinstance(cases, list) or len(cases) != len(EXPECTED_CASES): raise MaterializationError("case cardinality")
    for index, case in enumerate(cases):
        if not isinstance(case, dict): raise MaterializationError("malformed case")
        exact(case, CASE_FIELDS, f"case {index}")
        expected = EXPECTED_CASES[index]
        if _fixed_case(case) != _fixed_case(expected): raise MaterializationError(f"case {index}: fixed controls")
        width, height = case["width"], case["height"]
        if not isinstance(width, int) or not isinstance(height, int) or width <= 0 or height <= 0: raise MaterializationError("invalid dimensions")
        if case["bindings"] != _expected_binding(case): raise MaterializationError(f"case {case['name']}: bindings")
        if case["alpha_f32_word"] != "0x3f800000" or case["alpha_rgba8_byte"] != 255: raise MaterializationError(f"case {case['name']}: alpha contract")
        if case["input_immutable_exact_bits"] is not True: raise MaterializationError(f"case {case['name']}: immutability")
        count = width * height * 4
        source_input = case["input"]; source_expected = case["expected"]
        exact(source_input, INPUT_FIELDS, f"case {case['name']} input")
        exact(source_expected, EXPECTED_FIELDS, f"case {case['name']} expected")
        if source_input["width"] != width or source_input["height"] != height: raise MaterializationError(f"case {case['name']}: input dimensions")
        words(source_input["f32_words_le"], count, f"case {case['name']} input")
        words(source_expected["f32_words_le"], count, f"case {case['name']} expected")
        rgba = source_expected["rgba8_bytes"]
        if not isinstance(rgba, list) or len(rgba) != count or any(not isinstance(byte, int) or not 0 <= byte <= 255 for byte in rgba): raise MaterializationError(f"case {case['name']}: RGBA8 count/bytes")
        if hashlib.sha256(_pack(source_input["f32_words_le"])).hexdigest() != source_input["f32_sha256"] or source_input["f32_sha256"] != expected["input_f32_sha256"]: raise MaterializationError(f"case {case['name']}: input digest")
        if hashlib.sha256(_pack(source_expected["f32_words_le"])).hexdigest() != source_expected["f32_sha256"] or source_expected["f32_sha256"] != expected["expected_f32_sha256"]: raise MaterializationError(f"case {case['name']}: expected digest")
        if hashlib.sha256(bytes(rgba)).hexdigest() != source_expected["rgba8_sha256"] or source_expected["rgba8_sha256"] != expected["expected_rgba8_sha256"]: raise MaterializationError(f"case {case['name']}: RGBA digest")
    if doc["source_mutation_contract"] != {"source_relative_path":FACTORY_SOURCE,"source_sha256":FACTORY_SOURCE_SHA,"shader_relative_path":SOURCE,"shader_sha256":SOURCE_SHA,"canonical_factory_text_sha256":FACTORY_SHA,"execution":"each exact adapter source anchor/replacement is evaluated as a mutated juliaFactory and executed through bindCanonicalKernel/runPass"}: raise MaterializationError("source mutation contract")
    if doc["control_group"] != {"repeatability":{"case":"manual-smooth","identical_float32":True,"identical_rgba8":True},"input_immutability":{"case":"manual-smooth","unchanged":True},"input_lifetime":{"case":"manual-smooth","stable_after_independent_render":True},"independent_output_storage":{"case":"manual-distance-tile","distinct_data_objects":True,"distinct_backing_buffers":True},"public_direct_identity":True,"adapter_own_key":True}: raise MaterializationError("control group contract")
    profile = doc["cross_lane_assignment_profile"]
    exact(profile, {"status","contract","source_bound","anchor","replacement","mutated_factory_text_sha256"}, "cross-lane profile")
    if profile != {"status":"authenticated","contract":"derivative destination lanes are kept source-order sequential only for this exact adapter key","source_bound":"Julia GLSL source and juliaFactory adapter pins","anchor":"const nextDerivativeX = F32(2 * F32(F32(reHigh * derivativeX) - F32(imHigh * derivativeY)))\n      derivativeY = F32(2 * F32(F32(reHigh * derivativeY) + F32(imHigh * derivativeX)))\n      derivativeX = nextDerivativeX","replacement":"derivativeX = F32(2 * F32(F32(reHigh * derivativeX) - F32(imHigh * derivativeY)))\n      derivativeY = F32(2 * F32(F32(reHigh * derivativeY) + F32(imHigh * derivativeX)))","mutated_factory_text_sha256":"9fdd53914591d4bb4209094359c1450847beef8bf0426bf737c872de286d081e"}: raise MaterializationError("cross-lane profile contract")
    if doc["claim_boundaries"] != {"absolute_paths":"stable placeholders only","authority":"unmodified public juliaFactory adapter from immutable snapshot; C++ output does not participate","adapter":"adapter owns synth/julia:julia by authenticated canonical identity","mutations":"adapter source anchor replacements are executed authority mutations, not uniform perturbations","df64_low_carriers":"coordinates low-lane owner writes are structurally authenticated but do not change final Float32/RGBA8 pixels; pixel mutation count excludes those non-discriminable lanes"}: raise MaterializationError("claim boundaries contract")
    cardinality = doc["mutation_anchor_cardinality"]
    exact(cardinality, {"total","by_group","anchors"}, "mutation cardinality")
    if cardinality != {"total":len(EXPECTED_ORDER),"by_group":EXPECTED_GROUPS,"anchors":{name:1 for name in EXPECTED_ORDER}}: raise MaterializationError("mutation cardinality contract")
    ledger = doc["mutation_ledger"]
    search = doc["result_trap_search"]
    if not isinstance(ledger, list) or len(ledger) != len(EXPECTED_ORDER) or [item.get("name") for item in ledger] != EXPECTED_ORDER: raise MaterializationError("mutation order/cardinality")
    case_names = [case["name"] for case in cases]
    for mutation in ledger:
        name = mutation.get("name")
        mutation_fields = MUTATION_FIELDS | ({"source_span"} if name == "result-trap-number" else set())
        exact(mutation, mutation_fields, f"mutation {name}")
        if mutation["group"] not in EXPECTED_GROUPS or mutation["mechanism"] != EXPECTED_MECHANISMS[name] or mutation["anchor_occurrence_count"] != 1 or mutation["independent"] is not True: raise MaterializationError(f"mutation {name}: identity")
        if mutation["source_relative_path"] != FACTORY_SOURCE or mutation["source_sha256"] != FACTORY_SOURCE_SHA or mutation["canonical_factory_text_sha256"] != FACTORY_SHA: raise MaterializationError(f"mutation {name}: provenance")
        if name == "result-trap-number" and mutation["source_span"] != RESULT_TRAP_SOURCE_SPAN: raise MaterializationError(f"mutation {name}: authenticated source span")
        for field in ("source_anchor","replacement","anchor_sha256","replacement_sha256","mutated_factory_text_sha256"):
            if not isinstance(mutation[field], str) or not mutation[field]: raise MaterializationError(f"mutation {name}: {field}")
        if hashlib.sha256(mutation["source_anchor"].encode()).hexdigest() != mutation["anchor_sha256"] or hashlib.sha256(mutation["replacement"].encode()).hexdigest() != mutation["replacement_sha256"] or mutation["anchor_sha256"] != EXPECTED_ANCHORS[name] or mutation["replacement_sha256"] != EXPECTED_REPLACEMENTS[name] or mutation["mutated_factory_text_sha256"] != EXPECTED_MUTATED[name]: raise MaterializationError(f"mutation {name}: source hashes")
        results = mutation["results"]
        if not isinstance(results, list) or [row.get("case") for row in results] != case_names: raise MaterializationError(f"mutation {name}: result cases")
        result_hash = hashlib.sha256(json.dumps(results, separators=(",",":"), ensure_ascii=False).encode()).hexdigest()
        if mutation["result_sha256"] != EXPECTED_RESULTS[name] or result_hash != mutation["result_sha256"]: raise MaterializationError(f"mutation {name}: result hash")
        witnesses = [row["case"] for row in results if row.get("differs")]
        controls = [row["case"] for row in results if not row.get("differs")]
        if name == "result-trap-number":
            if mutation["witness_cases"] != [] or mutation["control_cases"] != controls or search["selected"]["changed_float32_lanes"] < 1 or search["selected"]["changed_rgba8_bytes"] < 1: raise MaterializationError(f"mutation {name}: bounded search witness/control cases")
        elif mutation["witness_cases"] != witnesses or mutation["control_cases"] != controls or not witnesses:
            raise MaterializationError(f"mutation {name}: witness/control cases")
        for row in results:
            exact(row, {"case","differs","changed_float32_lanes","changed_rgba8_bytes","float32_witness","rgba8_witness"}, f"mutation {name} result")
            if not isinstance(row["differs"], bool) or not isinstance(row["changed_float32_lanes"], int) or not isinstance(row["changed_rgba8_bytes"], int) or row["changed_float32_lanes"] < 0 or row["changed_rgba8_bytes"] < 0 or row["differs"] != (row["changed_float32_lanes"] > 0 or row["changed_rgba8_bytes"] > 0): raise MaterializationError(f"mutation {name}: result counts")
            count = cases[case_names.index(row["case"])] ["width"] * cases[case_names.index(row["case"])] ["height"] * 4
            for field, changed in (("float32_witness", row["changed_float32_lanes"]),("rgba8_witness", row["changed_rgba8_bytes"])):
                witness = row[field]
                if changed == 0:
                    if witness is not None: raise MaterializationError(f"mutation {name}: unexpected witness")
                else:
                    if not isinstance(witness, dict) or set(witness) != {"index","expected","actual"} or not isinstance(witness["index"], int) or not 0 <= witness["index"] < count or witness["expected"] == witness["actual"]: raise MaterializationError(f"mutation {name}: witness shape")
                    if field == "float32_witness" and (not isinstance(witness["expected"], str) or not HEX_WORD.fullmatch(witness["expected"]) or not isinstance(witness["actual"], str) or not HEX_WORD.fullmatch(witness["actual"])): raise MaterializationError(f"mutation {name}: Float32 witness")
                    if field == "rgba8_witness" and (not isinstance(witness["expected"], int) or not 0 <= witness["expected"] <= 255 or not isinstance(witness["actual"], int) or not 0 <= witness["actual"] <= 255): raise MaterializationError(f"mutation {name}: RGBA8 witness")
    if len({mutation["result_sha256"] for mutation in ledger}) != len(ledger): raise MaterializationError("mutation result hashes must be unique")
    if any(not any(row["changed_float32_lanes"] > 0 for row in mutation["results"]) or not any(row["changed_rgba8_bytes"] > 0 for row in mutation["results"]) for mutation in ledger if mutation["name"] != "result-trap-number"): raise MaterializationError("every pixel mutation requires Float32 and RGBA8 witnesses")
    return doc

def cpp_float(value):
    if isinstance(value, bool): return "true" if value else "false"
    if isinstance(value, int): return f"{value}.0F"
    return f"{float(value):.9g}F"

def cpp_number(value):
    if isinstance(value, bool): return "true" if value else "false"
    if isinstance(value, int): return f"{value}.0"
    return repr(float(value))

def cpp_binding(name, value):
    abi = EXPECTED_ABI[name]
    if abi == "int32": return str(int(value))
    if abi == "bool": return "true" if value else "false"
    return cpp_number(value)

def render(doc):
    import json as _json
    q = lambda value: _json.dumps(str(value), ensure_ascii=False)
    out = ["// Generated from the authenticated Julia JSON oracle.\n#pragma once\n#include <array>\n#include <cstddef>\n#include <cstdint>\n#include <span>\n#include <string_view>\n\nnamespace julia_oracle {\n"]
    out.append(f'inline constexpr std::string_view kProgramKey = {q(KEY)};\n')
    out.append(f'inline constexpr std::string_view kFactoryTextSha256 = {q(doc["factory"]["text_sha256"])};\n')
    out.append(f"inline constexpr std::array<std::string_view, {len(EXPECTED_NAMES)}> kBindingNames{{{{\n  " + ", ".join(q(name) for name in EXPECTED_NAMES) + "\n}};\n")
    out.append("struct BindingView { std::string_view name; std::string_view runtime_abi; std::string_view source_abi; }; using BindingAbiView = BindingView;\n")
    out.append(f"inline constexpr std::array<BindingView, {len(EXPECTED_NAMES)}> kBindingAbi{{{{\n")
    for name in EXPECTED_NAMES:
        out.append(f'  BindingView{{{q(name)}, {q(EXPECTED_ABI[name])}, {q(EXPECTED_SOURCE_ABI[name])}}},\n')
    out.append("}};\nstruct SourceBindingView { std::string_view name; std::string_view source_abi; }; using SourceBindingAbiView = SourceBindingView;\n")
    out.append(f"inline constexpr std::array<SourceBindingView, {len(EXPECTED_NAMES)}> kSourceBindingAbi{{{{\n")
    for name in EXPECTED_NAMES:
        out.append(f'  SourceBindingView{{{q(name)}, {q(EXPECTED_SOURCE_ABI[name])}}},\n')
    out.append("}};\n")
    out.append("struct BindingControl { std::array<float,2> resolution; std::array<float,2> tileOffset; std::array<float,2> fullResolution; double time; double cReal; double cImag; std::int32_t poi; std::int32_t outputMode; double centerX; double centerY; double rotation; std::int32_t iterations; double stripeFreq; std::int32_t trapShape; double lightAngle; std::int32_t cPath; double cSpeed; double cRadius; bool invert; double zoomSpeed; double zoomDepth; };\n")
    for index, case in enumerate(doc["render_cases"]):
        bindings = case["bindings"]
        pair = lambda name: "{" + ", ".join(cpp_float(value) for value in bindings[name]) + "}"
        values = [pair("resolution"), pair("tileOffset"), pair("fullResolution")] + [cpp_binding(name, bindings[name]) for name in EXPECTED_NAMES[3:]]
        out.append(f"inline constexpr BindingControl kCase{index}Bindings{{" + ", ".join(values) + "};\n")
        for label, data in (("Input", case["input"]["f32_words_le"]), ("Expected", case["expected"]["f32_words_le"]), ("Rgba8", case["expected"]["rgba8_bytes"])):
            ctype = "std::uint8_t" if label == "Rgba8" else "std::uint32_t"
            vals = ", ".join((str(value) + "U") if label == "Rgba8" else (value + "U") for value in data)
            out.append(f"inline constexpr std::array<{ctype}, {len(data)}> kCase{index}{label}{{{{\n  " + vals + "\n}};\n")
    out.append("struct CaseView { std::string_view name; std::size_t width; std::size_t height; BindingControl bindings; std::span<const std::uint32_t> input; std::string_view input_f32_sha256; std::span<const std::uint32_t> expected; std::string_view expected_f32_sha256; std::span<const std::uint8_t> rgba8; std::string_view expected_rgba8_sha256; std::string_view alpha_f32_word; std::uint8_t alpha_rgba8_byte; std::string_view output_alpha_f32_word; std::uint8_t output_alpha_rgba8_byte; bool input_immutable_exact_bits; };\n")
    out.append(f"inline constexpr std::array<CaseView, {len(doc['render_cases'])}> kCases{{{{\n")
    for index, case in enumerate(doc["render_cases"]):
        out.append(f'  CaseView{{{q(case["name"])}, {case["width"]}U, {case["height"]}U, kCase{index}Bindings, kCase{index}Input, {q(case["input"]["f32_sha256"])}, kCase{index}Expected, {q(case["expected"]["f32_sha256"])}, kCase{index}Rgba8, {q(case["expected"]["rgba8_sha256"])}, {q(case["alpha_f32_word"])}, {case["alpha_rgba8_byte"]}U, {q(case["alpha_f32_word"])}, {case["alpha_rgba8_byte"]}U, {str(case["input_immutable_exact_bits"]).lower()}}},\n')
    out.append("}};\n")
    diagnostic = doc["diagnostic_witnesses"][0]
    out.append(f"inline constexpr std::array<std::uint32_t, {len(diagnostic['canonical']['f32_words_le'])}> kDiagnosticCanonicalF32{{{{" + ", ".join(value + "U" for value in diagnostic["canonical"]["f32_words_le"]) + "}};\n")
    out.append(f"inline constexpr std::array<std::uint32_t, {len(diagnostic['instrumented']['f32_words_le'])}> kDiagnosticInstrumentedF32{{{{" + ", ".join(value + "U" for value in diagnostic["instrumented"]["f32_words_le"]) + "}};\n")
    out.append(f"inline constexpr std::array<std::uint8_t, {len(diagnostic['canonical']['rgba8_bytes'])}> kDiagnosticCanonicalRgba8{{{{" + ", ".join(str(value) + "U" for value in diagnostic["canonical"]["rgba8_bytes"]) + "}};\n")
    out.append(f"inline constexpr std::array<std::uint8_t, {len(diagnostic['instrumented']['rgba8_bytes'])}> kDiagnosticInstrumentedRgba8{{{{" + ", ".join(str(value) + "U" for value in diagnostic["instrumented"]["rgba8_bytes"]) + "}};\n")
    out.append("// diagnostic_witnesses are authenticated below.\nstruct DiagnosticWitnessView { std::string_view name; std::string_view source_anchor; std::string_view replacement; std::string_view anchor_sha256; std::string_view replacement_sha256; std::string_view instrumented_factory_sha256; std::size_t anchor_occurrence_count; std::size_t period_hit_count; std::span<const std::uint32_t> canonical_f32; std::span<const std::uint32_t> instrumented_f32; std::span<const std::uint8_t> canonical_rgba8; std::span<const std::uint8_t> instrumented_rgba8; };\n")
    out.append(f'inline constexpr std::array<DiagnosticWitnessView, {len(doc["diagnostic_witnesses"])}> kDiagnosticWitnesses{{{{\n')
    for witness in doc["diagnostic_witnesses"]:
        out.append(f'  DiagnosticWitnessView{{{q(witness["name"])}, {q(witness["source_anchor"])}, {q(witness["replacement"])}, {q(witness["anchor_sha256"])}, {q(witness["replacement_sha256"])}, {q(witness["instrumented_factory_text_sha256"])}, {witness["anchor_occurrence_count"]}U, {witness["period_hit_count"]}U, kDiagnosticCanonicalF32, kDiagnosticInstrumentedF32, kDiagnosticCanonicalRgba8, kDiagnosticInstrumentedRgba8}},\n')
    out.append("}};\nstruct RelationView { std::string_view name; std::string_view kind; std::string_view candidate_case; std::string_view control_case; bool identical_float32; bool identical_rgba8; std::size_t mutant_changed_float32_lanes; std::size_t mutant_changed_rgba8_bytes; std::size_t canonical_1000_loop_entries; std::size_t canonical_1001_loop_entries; std::size_t no_clamp_mutant_loop_entries; bool instrumented_canonical_1000_pixel_identical; bool instrumented_canonical_1001_pixel_identical; bool instrumented_mutant_pixel_identical; };\n")
    clamp = doc["relations"]["clamp_1001_vs_1000"]
    fallback_relations = doc["relations"]["fallbacks"]
    out.append(f"inline constexpr std::array<RelationView, {1 + len(fallback_relations)}> kRelations{{{{\n  RelationView{{{q(clamp['name'])}, {q(clamp['kind'])}, {q(clamp['candidate_case'])}, {q(clamp['control_case'])}, {str(clamp['identical_float32']).lower()}, {str(clamp['identical_rgba8']).lower()}, {clamp['mutant_candidate_changed_float32_lanes']}U, {clamp['mutant_candidate_changed_rgba8_bytes']}U, {clamp['canonical_1000_loop_entries']}U, {clamp['canonical_1001_loop_entries']}U, {clamp['no_clamp_mutant_loop_entries']}U, {str(clamp['instrumented_canonical_1000_pixel_identical']).lower()}, {str(clamp['instrumented_canonical_1001_pixel_identical']).lower()}, {str(clamp['instrumented_mutant_pixel_identical']).lower()}}},\n")
    for fallback in fallback_relations:
        control_label = {"outputMode-default":"outputMode=0", "trapShape-else":"trapShape=2", "cPath-explicit-default":"cPath=0"}[fallback["kind"]]
        out.append(f"  RelationView{{{q(fallback['name'])}, {q(fallback['kind'])}, {q(fallback['candidate_case'])}, {q(control_label)}, {str(fallback['identical_float32']).lower()}, {str(fallback['identical_rgba8']).lower()}, 0U, 0U, 0U, 0U, 0U, true, true, true}},\n")
    out.append("}};\nstruct RuntimeControlView { bool repeat_float32; bool repeat_rgba8; bool input_immutable; bool input_lifetime_stable; bool distinct_output_objects; bool distinct_backing_buffers; bool public_direct_identity; bool adapter_own_key; };\ninline constexpr RuntimeControlView kControlGroup{true, true, true, true, true, true, true, true};\n")
    selected = doc["result_trap_search"]["selected"]
    out.append("struct MixedPrecisionResultView { std::string_view field; std::string_view js_number_boundary; std::string_view f32_boundary; bool f32_applied_at_out_parameter; };\ninline constexpr MixedPrecisionResultView kResultTrapNumberBoundary{\"trapMin\", \"JS Number accumulator\", \"Math.fround only at the declared output boundary\", false};\n")
    selected_binding = selected["binding"]
    selected_pair = lambda name: "{" + ", ".join(cpp_float(value) for value in (selected_binding["width"], selected_binding["height"])) + "}"
    selected_values = [selected_pair("resolution"),
                       "{" + ", ".join(cpp_float(value) for value in (selected_binding["tileX"], selected_binding["tileY"])) + "}",
                       selected_pair("fullResolution")]
    selected_values.extend(cpp_binding(name, selected_binding[name]) for name in EXPECTED_NAMES[3:])
    out.append("inline constexpr BindingControl kResultTrapSearchBindings{" + ", ".join(selected_values) + "};\n")
    out.append(f"inline constexpr std::array<std::uint32_t, 4> kResultTrapSearchCanonicalF32{{{{" + ", ".join(value + "U" for value in selected["canonical"]["f32_words_le"]) + "}};\n")
    out.append(f"inline constexpr std::array<std::uint32_t, 4> kResultTrapSearchMutatedF32{{{{" + ", ".join(value + "U" for value in selected["mutated"]["f32_words_le"]) + "}};\n")
    out.append(f"inline constexpr std::array<std::uint8_t, 4> kResultTrapSearchCanonicalRgba8{{{{" + ", ".join(str(value) + "U" for value in selected["canonical"]["rgba8_bytes"]) + "}};\n")
    out.append(f"inline constexpr std::array<std::uint8_t, 4> kResultTrapSearchMutatedRgba8{{{{" + ", ".join(str(value) + "U" for value in selected["mutated"]["rgba8_bytes"]) + "}};\n")
    out.append("struct WitnessView { int index; std::string_view expected; std::string_view actual; };\nstruct ResultTrapSearchView { std::string_view selection_rule; std::string_view binding_name; std::size_t width; std::size_t height; BindingControl bindings; std::size_t order_index; std::size_t tested_candidates; std::size_t limit; std::size_t changed_float32_lanes; std::size_t changed_rgba8_bytes; WitnessView float32_witness; WitnessView rgba8_witness; std::span<const std::uint32_t> canonical_f32; std::span<const std::uint32_t> mutated_f32; std::span<const std::uint8_t> canonical_rgba8; std::span<const std::uint8_t> mutated_rgba8; };\n")
    trap_witness = lambda value: f"WitnessView{{{value['index']}, {q(value['expected'])}, {q(value['actual'])}}}"
    out.append(f"inline constexpr ResultTrapSearchView kResultTrapNumberSearch{{{q(doc['result_trap_search']['selection_rule'])}, {q(selected['binding']['name'])}, {selected['binding']['width']}U, {selected['binding']['height']}U, kResultTrapSearchBindings, {selected['order_index']}U, {doc['result_trap_search']['tested_candidates']}U, {doc['result_trap_search']['limit']}U, {selected['changed_float32_lanes']}U, {selected['changed_rgba8_bytes']}U, {trap_witness(selected['float32_witness'])}, {trap_witness(selected['rgba8_witness'])}, kResultTrapSearchCanonicalF32, kResultTrapSearchMutatedF32, kResultTrapSearchCanonicalRgba8, kResultTrapSearchMutatedRgba8}};\n")
    out.append("struct MutationResultView { std::string_view case_name; bool differs; std::size_t changed_float32_lanes; std::size_t changed_rgba8_bytes; WitnessView float32_witness; WitnessView rgba8_witness; };\n")
    for index, mutation in enumerate(doc["mutation_ledger"]):
        out.append(f"inline constexpr std::array<MutationResultView, {len(mutation['results'])}> kMutation{index}Results{{{{\n")
        for row in mutation["results"]:
            def witness(value):
                if value is None:
                    return "WitnessView{-1, {}, {}}"
                expected = q(value["expected"])
                actual = q(value["actual"])
                return f"WitnessView{{{value['index']}, {expected}, {actual}}}"
            out.append(f"  MutationResultView{{{q(row['case'])}, {str(row['differs']).lower()}, {row['changed_float32_lanes']}U, {row['changed_rgba8_bytes']}U, {witness(row['float32_witness'])}, {witness(row['rgba8_witness'])} }},\n")
        out.append("}};\n")
    for index, mutation in enumerate(doc["mutation_ledger"]):
        out.append(f"inline constexpr std::array<std::string_view, {len(mutation['witness_cases'])}> kMutation{index}WitnessCases{{{{\n")
        out.append("  " + ", ".join(q(value) for value in mutation["witness_cases"]) + ("\n" if mutation["witness_cases"] else "") + "}};\n")
        out.append(f"inline constexpr std::array<std::string_view, {len(mutation['control_cases'])}> kMutation{index}ControlCases{{{{\n")
        out.append("  " + ", ".join(q(value) for value in mutation["control_cases"]) + ("\n" if mutation["control_cases"] else "") + "}};\n")
    out.append("struct MutationView { std::string_view name; std::string_view group; std::string_view mechanism; std::string_view source_anchor; std::string_view source_span; std::string_view replacement; std::string_view anchor_sha256; std::string_view replacement_sha256; std::string_view mutated_factory_sha256; std::string_view result_sha256; bool independent; std::size_t anchor_occurrence_count; std::span<const std::string_view> witness_cases; std::span<const std::string_view> control_cases; std::span<const MutationResultView> results; };\n")
    out.append(f"inline constexpr std::array<MutationView, {len(doc['mutation_ledger'])}> kMutations{{{{\n")
    for index, mutation in enumerate(doc["mutation_ledger"]):
        out.append(f'  MutationView{{{q(mutation["name"])}, {q(mutation["group"])}, {q(mutation["mechanism"])}, {q(mutation["source_anchor"])}, {q(mutation.get("source_span", ""))}, {q(mutation["replacement"])}, {q(mutation["anchor_sha256"])}, {q(mutation["replacement_sha256"])}, {q(mutation["mutated_factory_text_sha256"])}, {q(mutation["result_sha256"])}, {str(mutation["independent"]).lower()}, {mutation["anchor_occurrence_count"]}U, kMutation{index}WitnessCases, kMutation{index}ControlCases, kMutation{index}Results}},\n')
    out.append("}};\n}\n")
    return "".join(out)

def _sidecar_hash(path):
    path = pathlib.Path(path)
    sidecar = pathlib.Path(f"{path}.sha256")
    if not path.is_file() or not sidecar.is_file() or sidecar.read_text() != f"{hashlib.sha256(path.read_bytes()).hexdigest()}  {path.name}\n": raise MaterializationError(f"sidecar drift: {path.name}")

def _verify_package_sidecars(include_target):
    paths = [ORACLE, PACKAGE / "julia-oracle-report.md", PACKAGE / "julia_oracle_generator.mjs", pathlib.Path(__file__)]
    if include_target:
        paths.append(TARGET)
    for path in paths:
        _sidecar_hash(path)

def _self_test():
    _verify_package_sidecars(include_target=True)
    doc = validate(strict_json(ORACLE.read_bytes()))
    checks = []

    def reject_raw(raw, label):
        import tempfile
        with tempfile.TemporaryDirectory(prefix="julia-oracle-forgery-") as raw_dir:
            candidate = pathlib.Path(raw_dir) / "forged.json"
            candidate.write_bytes(raw)
            pathlib.Path(f"{candidate}.sha256").write_text(f"{hashlib.sha256(raw).hexdigest()}  {candidate.name}\n")
            try:
                _sidecar_hash(candidate)
                validate(strict_json(raw))
            except (KeyError, MaterializationError, TypeError, ValueError):
                checks.append((label, True))
                return
        raise MaterializationError(f"self-test sentinel: forgery accepted: {label}")

    def reject(label, mutate):
        forged = copy.deepcopy(doc)
        mutate(forged)
        reject_raw(json.dumps(forged, separators=(",", ":"), ensure_ascii=False).encode(), label)

    def duplicate(label, marker):
        raw = ORACLE.read_bytes()
        if marker not in raw:
            raise MaterializationError(f"self-test marker missing: {label}")
        reject_raw(raw.replace(marker, marker + b"\n" + marker, 1), label)

    reject_raw(ORACLE.read_bytes().replace(b'"schema_version": 1,', b'"schema_version": 2,\n  "schema_version": 1,', 1), "duplicate top-level key")
    duplicate("duplicate factory key", b'    "name": "juliaFactory",')
    duplicate("duplicate case key", b'      "name": "manual-smooth",')
    duplicate("duplicate input key", b'        "width": 5,')
    duplicate("duplicate expected key", b'        "f32_words_le": [')
    duplicate("duplicate mutation result key", b'          "case": "manual-smooth",')
    duplicate("duplicate control key", b'      "case": "manual-smooth",')
    reject("schema_version", lambda d: d.__setitem__("schema_version", 2))
    reject("schema_version bool", lambda d: d.__setitem__("schema_version", True))
    reject("schema_version float", lambda d: d.__setitem__("schema_version", 1.0))
    reject("snapshot argument", lambda d: d["provenance"]["cpu_snapshot"].__setitem__("argument", "/tmp/forged"))
    reject("snapshot bool", lambda d: d["provenance"]["cpu_snapshot"].__setitem__("immutable_snapshot", 1))
    reject("snapshot float", lambda d: d["provenance"]["cpu_snapshot"].__setitem__("realpath_containment_checked", 1.0))
    reject("closure hash", lambda d: d["provenance"]["cpu_snapshot"]["import_closure"][0].__setitem__("sha256", "0"*64))
    reject("factory hash", lambda d: d["factory"].__setitem__("text_sha256", "0"*64))
    reject("binding names", lambda d: d["runtime_binding_names"].__setitem__(0, "forged"))
    reject("source ABI", lambda d: d["source_uniform_abi"].__setitem__("time", "int"))
    reject("exactness", lambda d: d["exactness_contract"].__setitem__("tolerance", "1e-6"))
    reject("comparer", lambda d: d["comparer_self_tests"]["cases"].__setitem__("good", False))
    reject("control group", lambda d: d["control_group"].__setitem__("adapter_own_key", False))
    reject("control bool trap", lambda d: d["control_group"]["repeatability"].__setitem__("identical_float32", 1))
    reject("case name", lambda d: d["render_cases"][0].__setitem__("name", "forged"))
    reject("case dimensions", lambda d: d["render_cases"][0].__setitem__("width", 99))
    reject("case width bool", lambda d: d["render_cases"][0].__setitem__("width", True))
    reject("case width float", lambda d: d["render_cases"][0].__setitem__("width", 5.0))
    reject("case integer bool", lambda d: d["render_cases"][0].__setitem__("poi", False))
    reject("case number bool", lambda d: d["render_cases"][0].__setitem__("time", True))
    reject("case number huge integer", lambda d: d["render_cases"][0].__setitem__("time", 10**1000))
    reject("case invert int", lambda d: d["render_cases"][0].__setitem__("invert", 1))
    reject("case alpha", lambda d: d["render_cases"][0].__setitem__("alpha_rgba8_byte", 0))
    reject("case alpha bool", lambda d: d["render_cases"][0].__setitem__("alpha_rgba8_byte", True))
    reject("case bindings", lambda d: d["render_cases"][0]["bindings"].__setitem__("time", 99.0))
    reject("binding integer float", lambda d: d["render_cases"][0]["bindings"].__setitem__("iterations", 80.0))
    reject("binding bool trap", lambda d: d["render_cases"][0]["bindings"].__setitem__("poi", True))
    reject("input dimensions bool", lambda d: d["render_cases"][0]["input"].__setitem__("width", True))
    def input_words(d):
        obj=d["render_cases"][0]["input"]; obj["f32_words_le"][0]="0x80000000"; obj["f32_sha256"]=hashlib.sha256(_pack(obj["f32_words_le"])).hexdigest()
    reject("input words with recomputed digest", input_words)
    def expected_words(d):
        obj=d["render_cases"][0]["expected"]; obj["f32_words_le"][0]="0x80000000"; obj["f32_sha256"]=hashlib.sha256(_pack(obj["f32_words_le"])).hexdigest()
    reject("expected words with recomputed digest", expected_words)
    def rgba(d):
        obj=d["render_cases"][0]["expected"]; obj["rgba8_bytes"][0]=(obj["rgba8_bytes"][0]+1)%256; obj["rgba8_sha256"]=hashlib.sha256(bytes(obj["rgba8_bytes"])).hexdigest()
    reject("RGBA with recomputed digest", rgba)
    reject("unknown input field", lambda d: d["render_cases"][0]["input"].__setitem__("extra", 1))
    reject("unknown expected field", lambda d: d["render_cases"][0]["expected"].__setitem__("extra", 1))
    reject("unknown mutation field", lambda d: d["mutation_ledger"][0].__setitem__("extra", 1))
    reject("mutation mechanism", lambda d: d["mutation_ledger"][0].__setitem__("mechanism", "uniform perturbation"))
    reject("mutation anchor", lambda d: d["mutation_ledger"][0].__setitem__("source_anchor", "forged"))
    reject("result-trap source span", lambda d: d["mutation_ledger"][-1].__setitem__("source_span", "julia.js:158:7-48"))
    reject("mutation anchor hash", lambda d: d["mutation_ledger"][0].__setitem__("anchor_sha256", "0"*64))
    reject("mutated factory hash", lambda d: d["mutation_ledger"][0].__setitem__("mutated_factory_text_sha256", "0"*64))
    reject("mutation result hash", lambda d: d["mutation_ledger"][0].__setitem__("result_sha256", "0"*64))
    reject("mutation anchor count bool", lambda d: d["mutation_ledger"][0].__setitem__("anchor_occurrence_count", True))
    reject("mutation anchor count float", lambda d: d["mutation_ledger"][0].__setitem__("anchor_occurrence_count", 1.0))
    reject("mutation result count bool", lambda d: d["mutation_ledger"][0]["results"][1].__setitem__("changed_float32_lanes", True))
    reject("mutation result count float", lambda d: d["mutation_ledger"][0]["results"][1].__setitem__("changed_rgba8_bytes", 1.0))
    reject("mutation result index bool", lambda d: d["mutation_ledger"][0]["results"][1]["float32_witness"].__setitem__("index", False))
    reject("mutation result index float", lambda d: d["mutation_ledger"][0]["results"][1]["float32_witness"].__setitem__("index", 0.0))
    def mutation_witness(d):
        for row in d["mutation_ledger"][0]["results"]:
            if row["float32_witness"] is not None:
                row["float32_witness"]["actual"] = row["float32_witness"]["expected"]
                return
        raise AssertionError("fixture lacks mutation witness")
    reject("mutation witness", mutation_witness)
    reject("cross-lane profile", lambda d: d["cross_lane_assignment_profile"].__setitem__("contract", "forged"))
    reject("claim authority", lambda d: d["claim_boundaries"].__setitem__("authority", "forged"))
    reject("absolute path", lambda d: d["claim_boundaries"].__setitem__("authority", "/tmp/forged"))
    good = {"width":1,"height":1,"f32_words_le":["0x00000000","0x3f800000","0x7fc00001","0x80000000"],"rgba8_bytes":[0,1,2,255]}
    comparer_tests = [("good", good, True), ("dimensions", {**good,"width":2}, False), ("short", {**good,"f32_words_le":good["f32_words_le"][:-1]}, False), ("long", {**good,"f32_words_le":[*good["f32_words_le"],"0x00000000"]}, False), ("RGBA count", {**good,"rgba8_bytes":good["rgba8_bytes"][:-1]}, False), ("RGBA mismatch", {**good,"rgba8_bytes":[1,1,2,255]}, False), ("signed zero", {**good,"f32_words_le":["0x00000000","0x3f800000","0x7fc00001","0x00000000"]}, False), ("NaN payload", {**good,"f32_words_le":["0x00000000","0x3f800000","0x7fc00002","0x80000000"]}, False)]
    for label, actual, should_pass in comparer_tests:
        try:
            compare_exact(good, actual)
            checks.append((f"comparer {label}", should_pass))
        except MaterializationError:
            checks.append((f"comparer {label}", not should_pass))
    for label, passed in checks:
        print(f"  [{'ok' if passed else 'FAIL'}] {label}")
    if len(checks) != EXPECTED_FORGE_CHECKS:
        raise MaterializationError(f"self-test sentinel: expected {EXPECTED_FORGE_CHECKS} checks, got {len(checks)}")
    print(f"Julia native oracle materializer self-test: {sum(passed for _, passed in checks)}/{len(checks)} pass; coordinated sidecars and sentinel verified")
    return 0 if all(passed for _, passed in checks) else 1

def main():
    parser = argparse.ArgumentParser(); parser.add_argument("--write", action="store_true"); parser.add_argument("--check", action="store_true"); parser.add_argument("--self-test", action="store_true"); args = parser.parse_args()
    if sum((args.write, args.check, args.self_test)) != 1: raise SystemExit("choose exactly one of --write, --check, or --self-test")
    if args.self_test: return _self_test()
    _verify_package_sidecars(include_target=not args.write)
    payload = ORACLE.read_bytes(); doc = validate(strict_json(payload)); rendered = render(doc)
    if args.write:
        TARGET.parent.mkdir(parents=True, exist_ok=True); TARGET.write_text(rendered); pathlib.Path(f"{TARGET}.sha256").write_text(f"{hashlib.sha256(rendered.encode()).hexdigest()}  {TARGET.name}\n"); _sidecar_hash(TARGET); print(f"julia include written ({len(rendered)} bytes)")
    elif not TARGET.is_file() or TARGET.read_text() != rendered: raise MaterializationError("generated include drift")
    else: print("julia materializer: ok")
    return 0

if __name__ == "__main__":
    try: raise SystemExit(main())
    except MaterializationError as exc: print(f"error: {exc}", file=sys.stderr); raise SystemExit(1)
