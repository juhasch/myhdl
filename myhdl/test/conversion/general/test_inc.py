from __future__ import absolute_import
import sys
import os
path = os.path
import random
from random import randrange
random.seed(2)

import pytest

import myhdl
from myhdl import *
from myhdl.conversion import verify


ACTIVE_LOW, INACTIVE_HIGH = bool(0), bool(1)

@block
def incRef(count, enable, clock, reset, n):
    """ Incrementer with enable.
    
    count -- output
    enable -- control input, increment when 1
    clock -- clock input
    reset -- asynchronous reset input
    n -- counter max value
    """
    @instance
    def logic():
        while 1:
            yield clock.posedge, reset.negedge
            if reset == ACTIVE_LOW:
                count.next = 0
            else:
                if enable:
                    count.next = (count + 1) % n
    return logic
                
@block
def inc(count, enable, clock, reset, n):
    
    """ Incrementer with enable.
    
    count -- output
    enable -- control input, increment when 1
    clock -- clock input
    reset -- asynchronous reset input
    n -- counter max value
    
    """
    
    @always(clock.posedge, reset.negedge)
    def incProcess():
        if reset == 0:
            count.next = 0
        else:
            if enable:
                count.next = (count + 1) % n
                
    return incProcess

@block
def inc2(count, enable, clock, reset, n):
    
    @always(clock.posedge, reset.negedge)
    def incProcess():
        if reset == ACTIVE_LOW:
            count.next = 0
        else:
            if enable:
                if count == n-1:
                    count.next = 0
                else:
                    count.next = count + 1
    return incProcess


@block
def incFunc(count, enable, clock, reset, n):
    def incFuncFunc(cnt, enable):
        count_next = intbv(0, min=0, max=n)
        count_next[:] = cnt
        if enable:
            count_next[:] = cnt + 1
        return count_next

    @always(clock.posedge, reset.negedge)
    def incFuncGen():
        if reset == ACTIVE_LOW:
            count.next = 0
        else:
            count.next = incFuncFunc(count, enable)

    return incFuncGen
    

@block
def incTask(count, enable, clock, reset, n):
    
    def incTaskFunc(cnt, enable, reset, n):
        if enable:
            cnt[:] = (cnt + 1) % n

    @instance
    def incTaskGen():
        cnt = intbv(0)[8:]
        while 1:
            yield clock.posedge, reset.negedge
            if reset == ACTIVE_LOW:
                cnt[:] = 0
                count.next = 0
            else:
                # print count
                incTaskFunc(cnt, enable, reset, n)
                count.next = cnt

    return incTaskGen


@block
def incTaskFreeVar(count, enable, clock, reset, n):
    
    def incTaskFunc():
        if enable:
            count.next = (count + 1) % n

    @always(clock.posedge, reset.negedge)
    def incTaskGen():
        if reset == ACTIVE_LOW:
           count.next = 0
        else:
            # print count
            incTaskFunc()

    return incTaskGen


@pytest.mark.parametrize('inc', [inc, inc2, incRef, incTask, incFunc])
@pytest.mark.verify_convert
@block
def test_inc(inc):

    NR_CYCLES = 201
      
    m = 8
    n = 2 ** m

    count = Signal(intbv(0)[m:])
    count_v = Signal(intbv(0)[m:])
    enable = Signal(bool(0))
    clock, reset = [Signal(bool(0)) for i in range(2)]


    inc_inst = inc(count, enable, clock, reset, n=n)

    @instance
    def clockgen():
        clock.next = 1
        for i in range(NR_CYCLES):
            yield delay(10)
            clock.next = not clock

    @instance
    def monitor():
        reset.next = 0
        enable.next = 1
        yield clock.negedge
        reset.next = 1
        yield clock.negedge
        while True:
            yield clock.negedge
            print(count)

    return inc_inst, clockgen, monitor
