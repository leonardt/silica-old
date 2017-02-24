Silica
======
### A Language for Constructing Finite State Machines in Hardware
Leonard Truong

Goals
-----
The design and implementation of finite state machines represent a critical
aspect of hardware design.  Silica aims to improve the productivity of hardware
designers by introducing a language for describing finite state machines (FSMs)
as coroutines.  Building an FSM in Silica should be easier to read and less
error prone than the Verilog counterpart.

Deliverables
----------------------
Our target application is a hardware image processing pipeline that contains a
diverse set of finite state machines including a camera protocol, a vga
controller, a memory interface, and image processing modules.  We aim to
replace as much of the state machine logic found in the existing pipeline with
FSMs written in Silica.

Alongside the demo application, Silica will drive the maintenance and
development of Magma and CoreIR.  To support Silica, Magma will be updated for
Python 3.  Silica will target CoreIR via Magma. To do this, CoreIR's C-api will
be wrapped for Python 3 and hooked into Magma.

Planned Contributions
---------------------
On the frontend, Silica introduces a software programming construct
(coroutines) to the domain of hardware languages.  We adjust coroutine
semantics to include the notion of time (what happens between yields occurs in
one clock cycle), creating a natural language for describing FSMs. The result
is readable code where state machine logic reads sequentially, rather than
branch heavy code with irregular jumps ("spaghetti code").

On the backend, Silica represents a case study in using Magma/CoreIR as a
target for domain specific hardware languages.  The power of the Magma/CoreIR
ecosystem is that many DSLs can be layered on top to provide flexible
programming environments.  Silica will drive the development of the internals
required to carry out this vision. For example, CoreIR will need Python
bindings for it's C-api, which should serve as a model for future bindings to
other languages.

Related Work
------------
Silica's design draws influences from many modern research projects in the
Hardware Languages space.
* [Chisel](https://chisel.eecs.berkeley.edu/) is a hardware construction
  language embedded in Scala. Many design decisions for Magma, Silica's target
  backend, were influenced by the Chisel project.
* [myhdl](http://www.myhdl.org/) and [pymtl](https://github.com/cornell-brg/pymtl)
  aim to embed a hardware design stack in Python.  They both leverage the power
  of Python as a general purpose programming language to improve the
  productivity of hardware designs. For example, they both leverage a Python
  unit testing framework for simulation and debugging. Silica reaps the same
  benefits of being embedding Python, while introducing a novel programming
  model for finite state machines.

# Timeline
* Completed  - Basic Frontend with Verilog backend (working UART TX/RX)
* March 3rd  - Magma Python3 Backend
* March 10th - Integrate with existing Rigel app
* March 17th - CoreIR/Magma integration

