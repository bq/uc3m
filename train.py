# Copyright 2018 Juan Abascal & Daniel Gonzalez. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# ==============================================================================

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import tensorflow as tf
import model
import logging
import input
from datetime import datetime

FLAGS = tf.app.flags.FLAGS

tf.app.flags.DEFINE_string('ckpt_dir', './data/checkpoints',
                           """Directory where to restore a model""")
tf.app.flags.DEFINE_string('save_dir', './data/train/flowers',
                           """Directory where to write event logs """
                           """and checkpoint.""")
tf.app.flags.DEFINE_string('log_dir', './data/train/log',
                           """Directory where to write event logs.""")
tf.app.flags.DEFINE_integer('max_steps', 10000,
                            """Number of batches to run.""")
tf.app.flags.DEFINE_integer('batch_size', 32,
                            """Size of batches.""")


def train():

    with tf.Graph().as_default() as g:
        global_step = tf.train.get_or_create_global_step()

        iterator = input.consume_tfrecord()
        images_batch, labels_batch = iterator.get_next()

        saver = tf.train.Saver()

        with tf.Session() as sess:
            saver.restore(sess, tf.train.latest_checkpoint(FLAGS.ckpt_dir))

        # Num_classes is None for fine tunning
        bottleneck, end_points = model.inception_v4(images_batch, num_classes=None, is_training=False)
        logits = model.fine_tuning(bottleneck, end_points)

        # TODO: Add a function to get train_op
        loss = model.loss(logits, labels_batch)
        optimizer = tf.train.GradientDescentOptimizer(2)
        train_op = optimizer.minimize(loss, global_step=global_step, var_list=tf.global_variables('fine_tuning'))

        with tf.Session() as sess:
            init = tf.global_variables_initializer()
            sess.run(init)
            sess.run([images_batch, labels_batch])

            # Tensorborad options
            train_writer = tf.summary.FileWriter(FLAGS.log_dir, g)

            logger = init_logger()
            logger.info("Training starts...")
            for i in range(0, FLAGS.max_steps):
                # Merge all summary variables for Tensorborad
                merge = tf.summary.merge_all()

                _, loss_val, summary = sess.run([train_op, loss, merge])

                if i % 10 is 0:
                    logger.info('Time: %s Loss: %f Step: %i', datetime.now(), loss_val, i)
                    # Write the summaries in the log file
                    train_writer.add_summary(summary, i)

                if i % 100 is 0:
                    saver.save(sess, FLAGS.save_dir)
                    logger.info("***** Saving model in: %s *****", FLAGS.save_dir)

            logger.info("Training ends...")


def main(argv=None):
    input.main(argv)
    train()


def init_logger():
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)

    return logger


if __name__ == "__main__":
    tf.app.run()
