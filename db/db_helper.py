# -*- coding: utf-8 -*-
import logging

from tornado import gen

@gen.coroutine
def insert_into_table(inst, executor, table_name, **kwargs):
    sql = "insert into %s (" % table_name
    values = " values( "
    i = 0
    length = len(kwargs)
    for (k,v) in kwargs.items():
        sql += "`%s`" % k
        values += "%s"
        if i != length - 1:
            sql += ","
            values += ","
        i += 1

    sql += ")"
    values += ")"

    sql += values
    logging.debug('insert sql %s ', sql)
    ret = yield executor.async_insert(inst, sql, kwargs.values())
    raise gen.Return(ret)
    
@gen.coroutine
def insert_into_table_return_id(inst, executor, table_name, **kwargs):
    sql = "insert into %s (" % table_name
    values = " values( "
    i = 0
    length = len(kwargs)
    for (k,v) in kwargs.items():
        sql += "`%s`" % k
        values += "%s"
        if i != length - 1:
            sql += ","
            values += ","
        i += 1

    sql += ")"
    values += ")"

    sql += values
    logging.debug('insert sql %s ', sql)
    ret = yield executor.async_insert_return_insert_id(inst, sql, kwargs.values())
    raise gen.Return(ret)

    
    
@gen.coroutine
def update_table_values(inst, executor, union_id, table_name, **kwargs):
    sql = "update %s set " % table_name
    i = 0
    for (k,v) in kwargs.items():
        sql += "`%s`=%%s" % (k,)
        if i != len(kwargs) - 1:
            sql += ","
        i += 1
        #kwargs[k] = self._convert_str(v)
    sql += " where id=%s" % union_id
    logging.debug("update sql %s" , sql)
    ret = yield executor.async_update(inst, sql, kwargs.values())
    raise gen.Return(ret)

@gen.coroutine
def delete_table_by_id(inst, executor,table_name, id):
    sql = "delete from %s" % table_name
    sql += "  where id=%s"
    
    logging.debug('delete sql %s ', sql)
    ret = yield executor.async_delete(inst, sql, (id,))
    raise gen.Return(ret)
    
@gen.coroutine   
def select_from_table(inst, executor, table_name, order_sql=None, **kwargs):
    sql = "select * from %s " % table_name
    sql += "where "
    i = 0
    for (k,v) in kwargs.items():
        sql += " `%s`=%%s " % (k,)
        if i != len(kwargs) - 1:
            sql += " and "
        i += 1

    if order_sql:
        sql += order_sql

    ret = executor.async_select(inst, sql, kwargs.values())
    raise gen.Return(ret)


@gen.coroutine
def is_table_exists(inst, executor, table_name):
    sql = "SELECT table_name FROM information_schema.TABLES WHERE table_name=%s"
    ret = yield executor.async_select(inst, sql, table_name)
    raise gen.Return(ret)