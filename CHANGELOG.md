# Changelog

## [0.1.0](https://github.com/midsonlajeanty/natcashify/compare/v0.1.0...v0.1.0) (2026-10-21)


### Features

* **core:** add a callback signing helper for tests ([d350501](https://github.com/midsonlajeanty/natcashify/commit/d350501cd0ff826908787577e5b0412d0ed7483c))
* **core:** add errors and merchant configuration ([4f28157](https://github.com/midsonlajeanty/natcashify/commit/4f281573c5fa6f4a8792ba5d06a6eed436a8f6e6))
* **core:** add pluggable sync and async HTTP transports ([724d328](https://github.com/midsonlajeanty/natcashify/commit/724d328d0daa71294fad28787fac12c366f43bfb))
* **core:** add sync and async NatCash clients ([e3c4190](https://github.com/midsonlajeanty/natcashify/commit/e3c4190e63b9a0b4f8041c729435df11d29acb7a))
* **core:** build and parse NatCash requests without I/O ([6932117](https://github.com/midsonlajeanty/natcashify/commit/693211721d7f3324f85af6b5c09bbcee37d8e715))
* **core:** sign requests and callbacks like the PHP SDK ([c6195a0](https://github.com/midsonlajeanty/natcashify/commit/c6195a0ab9fa8f077f636bdc1920ac85a8a0bc55))
* **core:** use UUIDv7 request ids ([1082bfb](https://github.com/midsonlajeanty/natcashify/commit/1082bfbe407720df2106f3a26a08612fc566e79f))
* **django:** add the Django adapter ([b137471](https://github.com/midsonlajeanty/natcashify/commit/b13747143d69b2dfdd08eeaff1bf879a3c847f46))
* expose the core API from the natcashify facade ([81dde6f](https://github.com/midsonlajeanty/natcashify/commit/81dde6f417ff673090b5a91ce9f38acf50ae312b))
* **fastapi:** add the FastAPI adapter ([36e7863](https://github.com/midsonlajeanty/natcashify/commit/36e7863fe09099c0e076d5d273fc104228bca9a9))
* **flask:** add the Flask extension ([d0cdd07](https://github.com/midsonlajeanty/natcashify/commit/d0cdd0777f955dc38170e61dc0b303bef4f1cb15))


### Bug Fixes

* **core:** bound huge integer expiry values ([997668a](https://github.com/midsonlajeanty/natcashify/commit/997668a9e365ccf05b3f1c1bac96afbb927858e7))
* **core:** mask the callback key in the config repr ([21f71a3](https://github.com/midsonlajeanty/natcashify/commit/21f71a38ed6afae2d32a3dc299143bb10f978dc0))
* **core:** reject malformed callbacks and responses with SDK errors ([28744c3](https://github.com/midsonlajeanty/natcashify/commit/28744c36772425fb0e9b5de30cb4e6f2532f7a38))
* **core:** reject non-string and blank credentials ([3dc2500](https://github.com/midsonlajeanty/natcashify/commit/3dc250084494b2ffefab2077b863495eb1a46280))
* **core:** require a boolean sandbox flag ([4189d56](https://github.com/midsonlajeanty/natcashify/commit/4189d56fe3599687018b2511fa943c314fe2acda))
* **core:** tighten order number and amount parsing ([9f2ec16](https://github.com/midsonlajeanty/natcashify/commit/9f2ec1615e420b56b071952467f342a6cc0f8f46))
* **core:** validate fee and language types ([8d79237](https://github.com/midsonlajeanty/natcashify/commit/8d792376623a88c3af13fe42591257d92b9d7e2d))
* **core:** wrap every transport failure in TransportError ([1a7885b](https://github.com/midsonlajeanty/natcashify/commit/1a7885bcec04fa1fb9ca3ebc767b87f2ff8dae3e))
* **django:** use the async client in async callback views ([063a3c6](https://github.com/midsonlajeanty/natcashify/commit/063a3c6d7a67d2d10455144964d4981b3af2b157))
* **flask:** explain a missing init_app ([b4d6904](https://github.com/midsonlajeanty/natcashify/commit/b4d690419e92c347c3a9e4bca7208b43c7822246))


### Documentation

* add the documentation site, READMEs and examples ([50200f1](https://github.com/midsonlajeanty/natcashify/commit/50200f160c02ad0dcb91f9340f65b3483271670f))
* fix the moncashify amount conversion and the Django minimum ([5e57991](https://github.com/midsonlajeanty/natcashify/commit/5e579915ceb0fc5f28968beb17ee30fabb66af7f))
* make the callback example idempotent ([9641a7c](https://github.com/midsonlajeanty/natcashify/commit/9641a7cbdbc00205614b120043f2778d6ce10275))
