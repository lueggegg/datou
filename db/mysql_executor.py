# -*- coding: utf-8 -*-

from tornado import gen


class MySQLExecutorException(Exception):
    def __init__(self, message):
        self._message = message

    def __str__(self):
        return self._message


class MySQLExecutor:
    def __init__(self, *args, **kwargs):
        pass

    @gen.coroutine
    def async_select(self, myinst, sql, vals=None):
        ret = []

        cursor = yield myinst.execute(sql, vals)
        for row in cursor:
            tmp = {}
            for i in range(0, len(row)):
                tmp[cursor.description[i][0]] = row[i]

            ret.append(tmp)

        raise gen.Return(ret)

    @gen.coroutine
    def async_delete(self, myinst, sql, vals=None):
        cursor = yield myinst.execute(sql, vals)
        ret = cursor.rowcount
        raise gen.Return(ret)

    @gen.coroutine
    def async_update(self, myinst, sql, vals=None):
        ret = None
        if not vals:
            vals = None
        cursor = yield myinst.execute(sql, vals)
        ret = cursor.rowcount
        raise gen.Return(ret)

    @gen.coroutine
    def async_insert(self, myinst, sql, vals, **kwargs):
        ret = None
        if not vals:
            vals = None
        cursor = yield myinst.execute(sql, vals)
        ret = cursor.lastrowid
        raise gen.Return(ret)

    @gen.coroutine
    def async_insert_return_insert_id(self, myinst, sql, vals, **kwargs):
        ret = None
        if not vals:
            vals = None
        cursor, insert_id = yield myinst.execute_whit_insert_id(sql, vals)
        raise gen.Return(insert_id)

    @gen.coroutine
    def batch_execute(self, myinst, sql_and_vals, **kwargs):
        ret = []
        rollback = False
        trans = yield myinst.begin()

        for v in sql_and_vals:
            sql = v[0]
            vals = v[1]

            if not vals:
                vals = None

            try:
                cursor = yield trans.execute(sql, vals)
                rollback = True
                rcount = cursor.rowcount
                rows = []
                last_row_id = cursor.lastrowid
                for row in cursor:
                    tmp = {}
                    for i in range(0, len(row)):
                        tmp[cursor.description[i][0]] = row[i]
                    rows.append(tmp)
                ret.append((rcount, last_row_id, rows))
                cursor.close()
            except Exception, e:
                if rollback:
                    yield trans.rollback()
                    raise e
        yield trans.commit()
        raise gen.Return(ret)

