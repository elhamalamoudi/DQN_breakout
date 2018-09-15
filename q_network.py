
import tensorflow as tf
import numpy as np
# ===========================
#   Actor and Critic DNNs
# ===========================



class Network(object):
    """
    Input to the network is the state, output is the action
    under a deterministic policy.
    The output layer activation is a tanh to keep the action
    between -2 and 2
    """

    def __init__(self, sess, SIZE_FRAME, action_dim, learning_rate, tau, device):
        self.sess = sess
        self.a_dim = action_dim
        self.learning_rate = learning_rate
        self.tau = tau
        self.currentState = -1.
        self.device = device
        self.SIZE_FRAME = SIZE_FRAME
        
        # Q network
        self.inputs, self.out = self.create_q_network('q')
        self.network_params = tf.trainable_variables()

        # Target Network
        self.target_inputs, self.target_out = self.create_q_network('q_target')

        self.target_network_params = tf.trainable_variables()[
            len(self.network_params):]

        # Op for periodically updating target network with online network
        # weights
        self.update_target_network_params = \
            [self.target_network_params[i].assign(tf.multiply(self.network_params[i], self.tau) +
                                                  tf.multiply(self.target_network_params[i], 1. - self.tau))
                for i in range(len(self.target_network_params))]

        with tf.device(self.device):
            
            self.predicted_q_value = tf.placeholder(tf.float32, [None, self.a_dim])
            # Define loss and optimization Op
            self.loss = tf.reduce_mean(tf.square(tf.subtract(self.predicted_q_value,self.out)))
            self.optimize = tf.train.AdamOptimizer(self.learning_rate).minimize(self.loss)

        self.num_trainable_vars = len(self.network_params) + len(self.target_network_params)

    def create_q_network(self, scope):

        with tf.device(self.device):
            with tf.variable_scope(scope): 
                 
                # Xavier initialization: 
                regularizer = tf.contrib.layers.l2_regularizer(0.1)
                W_conv1 = tf.get_variable("W_conv1_a", shape=[4,4,4,32],regularizer = regularizer, initializer=tf.contrib.layers.xavier_initializer_conv2d())
                b_conv1 = tf.Variable(tf.zeros([32]))
                W_conv2 = tf.get_variable("W_conv2_a", shape=[4,4,32,32],regularizer = regularizer, initializer=tf.contrib.layers.xavier_initializer_conv2d())
                b_conv2 = tf.Variable(tf.zeros([32]))
                W_conv3 = tf.get_variable("W_conv3_a", shape=[3,3,32,32],regularizer = regularizer, initializer=tf.contrib.layers.xavier_initializer_conv2d())
                b_conv3 = tf.Variable(tf.zeros([32]))
                W_fc1 = tf.get_variable("W_fc1_a", shape=[1568,200],regularizer = regularizer, initializer=tf.contrib.layers.xavier_initializer())
                b_fc1 = tf.Variable(tf.zeros([200]))
                W_fc2 = tf.Variable(np.random.uniform(size=(200,self.a_dim),low= -0.0003, high=0.0003 ).astype(np.float32))
                b_fc2 = tf.Variable(tf.zeros([self.a_dim])) 
                
                # input layer

                stateInput = tf.placeholder(tf.float32, shape=[None,self.SIZE_FRAME,self.SIZE_FRAME,4]) # 84,84,4
                # COnv layers
                h_conv1 = tf.nn.relu(self.conv2d(stateInput,W_conv1,4) + b_conv1)
                h_conv2 = tf.nn.relu(self.conv2d(h_conv1,W_conv2,2) + b_conv2)
                h_conv3 = tf.nn.relu(self.conv2d(h_conv2,W_conv3,1) + b_conv3)
                h_conv3_flat = tf.reshape(h_conv3,[-1,1568])
                h_fc1 = tf.nn.relu(tf.matmul(h_conv3_flat,W_fc1) + b_fc1)
                out = tf.matmul(h_fc1,W_fc2) + b_fc2
                
        self.saver = tf.train.Saver()
        return stateInput, out

        
    def train(self, inputs, predicted_q_value):
        self.sess.run(self.optimize, feed_dict={
            self.inputs: inputs,
            self.predicted_q_value: predicted_q_value
        })

    def predict(self, inputs):
        return self.sess.run(self.out, feed_dict={
            self.inputs: inputs
        })

    def predict_target(self, inputs):
        return self.sess.run(self.target_out, feed_dict={
            self.target_inputs: inputs
        })

    
    def update_target_network(self):
        self.sess.run(self.update_target_network_params)

    def get_num_trainable_vars(self):
        return self.num_trainable_vars
    
    def save(self):
        self.saver.save(self.sess,'model.ckpt')
        #saver.save(self.sess,'actor_model.ckpt')
        print("Model saved in file: model")

    
    def recover(self):
        self.saver.restore(self.sess,'model.ckpt')
        #saver.restore(self.sess,'critic_model.ckpt')
    
    def conv2d(self,x, W, stride):
        return tf.nn.conv2d(x, W, strides = [1, stride, stride, 1], padding = "VALID")