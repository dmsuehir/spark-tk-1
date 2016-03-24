package org.trustedanalytics.at.context

import org.apache.spark.api.java.JavaSparkContext
import org.apache.spark.org.trustedanalytics.at.frame.FrameRdd
import org.trustedanalytics.at.frame.Frame
import org.trustedanalytics.at.frame.ops.Load

class Context(jsc: JavaSparkContext) extends Serializable {

  private val sc = jsc.sc

  def helloWorld(): String = "Hello from TK"

  def loadFrame(path: String): Frame = {
    val frameRdd: FrameRdd = Load.loadParquet(path, sc)
    new Frame(frameRdd, frameRdd.frameSchema)
  }
}
