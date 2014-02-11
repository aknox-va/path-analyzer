__author__ = 'Aknox'

from sys_tracing import allow_tracking


def a():
    b()
    c()
    d()


def b():
    pass


def c():
    b()
    d()


def d():
    b()


@allow_tracking
def k():
    a()
    b()
    c()
    d()

k()