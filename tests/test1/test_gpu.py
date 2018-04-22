
import tensorflow as tf
import pandas as pd
import time


def run_fct(*args):
    for i in range(20):
        c = []
        for d in ['/device:GPU:2', '/device:GPU:3', '/device:GPU:1', '/device:GPU:0']:
            with tf.device(d):
                a = tf.constant([1.0, 2.0, 3.0, 4.0, 5.0, 6.0], shape=[2, 3])
                b = tf.constant([1.0, 2.0, 3.0, 4.0, 5.0, 6.0], shape=[3, 2])
                c.append(tf.matmul(a, b))
        with tf.device('/cpu:0'):
            sum = tf.add_n(c)
            # Creates a session with log_device_placement set to True.
        sess = tf.Session(config=tf.ConfigProto(log_device_placement=True))
        time.sleep(1)
        # Runs the op.
        print(sess.run(sum))
    print(args)
    pd.DataFrame([1, 2, 3]).to_csv("result.csv")


if __name__ == "__main__":
    import slurmlib

    a = slurmlib.Job(gpu=4, cpu=None,
                     time="1:00:00", queue="besteffort", environment="py35",
                     request_node=False, folder_to_send=".", ignore_files20MB=True,
                     destination_folder="new", keep_bundle=True)
    a.run(run_fct, 1, 2, 3, 4)
