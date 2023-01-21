# QuakeMapBackend Coding Standards

## Summary

The key words "MUST", "MUST NOT", "REQUIRED", "SHALL", "SHALL NOT",
"SHOULD", "SHOULD NOT", "RECOMMENDED",  "MAY", and "OPTIONAL"
in this document are to be interpreted as described in RFC 2119.

The key word "program" in this document is to be interpreted as a file that is executable.

The key word "API" in this document is to be interpreted as an endpoint that a router exposes.

This document outlines conventions/regulations that **MUST** be followed during coding.

Failure to comply with these conventions can prevent the program from starting.

## 1. Assets

The _assets_ folder **SHALL** store files that are:

- not a program, and
- used within the program as **reference**.

The folder **SHOULD NOT** store files that will be modified during the execution. There could be exceptions, such as
a self-updating mechanism to update all the assets; however, these **SHALL** be documented in _Update.md_.

The _Update.md_ **SHALL** contain information about the update schedule and the update method of assets.

## 2. Config

The _config_ folder **SHALL** store files that are either:

- a program that parses configuration files (**RECOMMENDED** to be _init.py_), or
- the configuration files that will be used upon execution. (**RECOMMENDED** to be _\<environment\>.\<extension\>_)

The configuration files **MUST NOT** be modified during execution, and **SHOULD** only be changed by the user.

The initialization program **SHALL** parse the configuration files and initialize the program.
The initialization program **MUST NOT** be called by anything other than the entrypoint of the program.

The initialization program **MUST NOT** import/reference other modules in the program,
either directly or indirectly (local), except for _models_, _env_ and _sdk_.

## 3. Internal

The _internal_ folder **SHOULD** store files that are either:

- a program that will be used frequently within the program, and do not belong to any of the _APIs_ exposed; or,
- a program that manages the execution/schedule of the whole program.

The programs contained here **SHOULD NOT** directly import other modules in the program except for _model_ and _sdk_.
The program contained here **MAY** use indirect/local import to reference other modules in the program.

The programs contained here **SHOULD** be registered as a globally available instance under _env_.

There is exception, however, for the second type of the programs contained here.
Under this case, a program **MAY** import/reference other modules, either directly or indirectly.

## 4. Model

The _model_ folder **SHALL** store files that is:

- a program that describes the structure of data.

The programs contained here **SHALL NOT** reference/import any other modules in the program or the libraries unless
necessary.
Generally, it **SHALL NOT** import any other modules, and it **MAY** import modules that defines the foundation for the
structures, or defines the data types.

The program contained here **SHALL** enlist publicly available models clearly.

## 5. Modules

The _modules_ folder **SHALL** store files that are either:

- a program that serves as the backend of an _API_, or
- a program that modifies the data/serves as a middleware in the API.

For the first type of the programs contained here, they **MAY** reference any module if needed.
They **SHALL** follow a fixed foundation, usually defined in _base_module.py_.

For the second type of the programs contained here, they **SHALL NOT** reference _routers_,
either directly or indirectly.
They **SHOULD** import other modules such as _env_ using local import.

They **SHOULD** expose their methods using classmethods, etc. that are stateless.
They **SHOULD NOT** modify anything in program, and **SHOULD** only perform operations using the given data.
They **SHALL** return something in the end.

## 6. Routers

The _routers_ folder **SHALL** store files that is:

- an endpoint that can be accessed by the user.

The programs contained here **SHALL** always return something in the end.

The programs contained here **MAY** modify/process the data, either by middleware or by themselves.

## 7. Tools

The _tools_ folder **SHALL** store files that are:

- a program that is not required during normal execution, and
- a program that serves as utilities.

The programs contained here **SHALL NOT** be referenced/imported by any modules in the program.
The programs contained here **SHALL NOT** reference/import any modules in the program.

The programs contained here **MAY** access/modify _assets_.

The programs contained here **SHALL** have a dedicated entrypoint.