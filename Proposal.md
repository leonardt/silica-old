Silica
======
### A Language for Constructing Finite State Machines in Hardware
Leonard Truong

```
* What is the goal of the project? What problem are you trying to solve?
```

The design and implementation of finite state machines represent a critical
aspect of hardware design.  Silica aims to improve the productivity of hardware
designers by introducing a language for describing finite state machines (FSMs)
as coroutines.  Building an FSM in Silica should be less verbose and less error
prone than the Verilog counterpart.

```
* What do you hope to show when you are done? What are your deliverables?
```
Our target application is a hardware image processing pipeline that contains a
diverse set of finite state machines including a camera protocol, a vga
controller, and image processing modules.  We aim to replace as much of the
state machine logic found in the existing pipeline with FSMs written in Silica.

```
* Why is it interesting, challenging, or important about the project?
```
On the frontend, Silica introduces a software programming construct
(coroutines) to the domain of hardware languages.  We adjust coroutine
semantics to include the notion of time (what happens between yields occurs in
one clock cycle), creating a natural language of describing FSMs in hardware.

On the backend, Silica represents a case study in using Magma as a target for
domain specific hardware languages.  The power of the Magma ecosystem is that
many DSLs can be layered on top to provide flexible programming environments.
Silica will demonstrate how to use Magma as a DSL target, as well as driving
improvements in the Magma design and implementation.


```
* What previous work has been performed in this area?
  What resources do you plan on drawing upon?
```
Related Work
------------
### Hardware Description Languages
* [Chisel](https://chisel.eecs.berkeley.edu/) - a hardware construction language embedded in Scala
* [pshdl](http://pshdl.org/) - plain, simple HDL
* [myhdl](http://www.myhdl.org/) - turns Python into a hardware description and verification language


# Timeline
* Completed  - Basic Frontend with Verilog backend (working UART TX/RX)
* March 3rd  - Magma Backend
* March 10th - Integrate with existing Rigel app (on Ross's board)
* March 17th - CoreIR/Magma integration

