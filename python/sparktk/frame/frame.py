from pyspark.rdd import RDD

from sparktk.frame.pyframe import PythonFrame
from sparktk.frame.schema import schema_to_python, schema_to_scala


class Frame(object):

    def __init__(self, context, source, schema=None):
        self._context = context
        if self._is_scala_frame(source):
            self._frame = source
        elif self.is_scala_rdd(source):
            scala_schema = schema_to_scala(self._context.sc, schema)
            self._frame = self.create_scala_frame(self._context.sc, source, scala_schema)
        else:
            if not isinstance(source, RDD):
                source = self._context.sc.parallelize(source)
            if schema:
                self.validate_pyrdd_schema(source, schema)
            self._frame = PythonFrame(source, schema)

    def validate_pyrdd_schema(self, pyrdd, schema):
        pass

    @staticmethod
    def create_scala_frame(sc, scala_rdd, scala_schema):
        """call constructor in JVM"""
        return sc._jvm.org.trustedanalytics.at.frame.Frame(scala_rdd, scala_schema)

    def _frame_to_scala(self, python_frame):
        """converts a PythonFrame to a Scala Frame"""
        sc = self._context.sc
        scala_schema = schema_to_scala(sc, python_frame.schema)
        scala_rdd = sc._jvm.org.trustedanalytics.at.frame.rdd.PythonJavaRdd.pythonToScala(python_frame.rdd._jrdd, scala_schema)
        return self.create_scala_frame(sc, scala_rdd, scala_schema)

    def _is_scala_frame(self, item):
        return self._context._jutils.is_jvm_instance_of(item, self._context.sc._jvm.org.trustedanalytics.at.frame.Frame)

    def is_scala_rdd(self, item):
        return self._context._jutils.is_jvm_instance_of(item, self._context.sc._jvm.org.apache.spark.rdd.RDD)

    def is_python_rdd(self, item):
        return isinstance(item, RDD)

    @property
    def _is_scala(self):
        """answers whether the current frame is backed by a Scala Frame"""
        return self._is_scala_frame(self._frame)

    @property
    def _is_python(self):
        """answers whether the current frame is backed by a _PythonFrame"""
        return not self._is_scala

    @property
    def _scala(self):
        """gets frame backend as Scala Frame, causes conversion if it is current not"""
        if self._is_python:
            # convert PythonFrame to a Scala Frame"""
            sc = self._context.sc
            scala_schema = schema_to_scala(sc, self._frame.schema)
            scala_rdd = sc._jvm.org.trustedanalytics.at.frame.rdd.PythonJavaRdd.pythonToScala(self._frame.rdd._jrdd, scala_schema)
            self._frame = self.create_scala_frame(sc, scala_rdd, scala_schema)
        return self._frame

    @property
    def _python(self):
        """gets frame backend as _PythonFrame, causes conversion if it is current not"""
        if self._is_scala:
            # convert Scala Frame to a PythonFrame"""
            scala_schema = self._frame.schema()
            java_rdd =  self._context.sc._jvm.org.trustedanalytics.at.frame.rdd.PythonJavaRdd.scalaToPython(self._frame.rdd(), scala_schema)
            python_schema = schema_to_python(self._context.sc, scala_schema)

            # HACK
            # todo: figure out serialization such that we don't get tuples back, but lists, to avoid this full pass :(

            def to_list(row):
                return list(row)
            python_rdd = RDD(java_rdd, self._context.sc).map(to_list)
            self._frame = PythonFrame(python_rdd, python_schema)
        return self._frame


    ##########################################################################
    # API
    ##########################################################################

    @property
    def rdd(self):
        """pyspark RDD  (causes conversion if currently backed by a Scala RDD)"""
        return self._python.rdd

    @property
    def schema(self):
        if self._is_scala:
            return schema_to_python(self._context.sc, self._frame.schema())  # need ()'s on schema because it's a def in scala
        return self._frame.schema

    def append_csv_file(self, file_name, schema, separator=','):
        self._scala.appendCsvFile(file_name, schema_to_scala(self._context.sc, schema), separator)

    def export_to_csv(self, file_name):
        self._scala.exportToCsv(file_name)

    def count(self):
        if self._is_scala:
            return int(self._scala.count())
        return self.rdd.count()

    # Frame Operations

    from sparktk.frame.ops.add_columns import add_columns
    from sparktk.frame.ops.bin_column import bin_column
    from sparktk.frame.ops.drop_rows import drop_rows
    from sparktk.frame.ops.filter import filter
    from sparktk.frame.ops.inspect import inspect
    from sparktk.frame.ops.save import save
    from sparktk.frame.ops.take import take



