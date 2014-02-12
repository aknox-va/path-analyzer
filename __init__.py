__author__ = 'Aknox'

# Tests
if __name__ == '__main__':
    from sys_tracing import allow_tracking

    def a():
        b()
        c()
        d()
        return 'a'

    def b():
        return 'b'

    def c():
        b()
        d()
        return 'c'

    def d():
        b()
        return 'd'

    @allow_tracking
    def k():
        a()
        b()
        c()
        d()

    k()