import mysql_executor

class DAOException(Exception):
    def __init__(self, message):
        self._message = message

    def __str__(self):
        return self._message


class BaseDAO:
    def __init__(self, *args, **kwargs):
        self.desc = 'base'
        if len(args) > 0:
            self._inst_mgr = args[0]
        else:
            self._inst_mgr = kwargs["inst_mgr"]

        self._executor = mysql_executor.MySQLExecutor()

    def _get_inst(self, readonly=False):
        inst = None

        if readonly:
            inst = self._inst_mgr.get_inst_by_random(readonly)

        # Second try get rw instance
        if not inst:
            inst = self._inst_mgr.get_inst_by_random()

        if not inst:
            raise DAOException("Get %s mysql instance error, not found" % self.desc)
        return inst