"""
File for the attention model created
"""
from __future__ import print_function

import tensorflow as tf
from tensorflow.keras.models import Sequential, Model
from tensorflow.keras.layers import LSTM, Bidirectional, Conv1D, Attention, GlobalAveragePooling1D, GlobalMaxPool1D, \
    Dropout, Layer, Dense, MaxPool1D
from tensorflow.keras.losses import BinaryCrossentropy, CategoricalCrossentropy, SparseCategoricalCrossentropy
from tensorflow.keras.regularizers import l2, l1, l1_l2
from sklearn.metrics import classification_report, accuracy_score, roc_auc_score
from tensorflow.keras.callbacks import ReduceLROnPlateau, EarlyStopping, ModelCheckpoint
from basemodel import BaseModel

SEED = 42


class CNNRNNModel(BaseModel):
    '''Class that contain the attention model created for the Proppy database.
    '''

    def __init__(self, batch_size, epochs, filters, kernel_size, optimizer, max_sequence_len, lstm_units,
                 path_train, path_test, path_dev, vocab_size, learning_rate=1e-3, pool_size=4, rate=0.2,
                 embedding_size=300, max_len=1900, load_embeddings=True, buffer_size=3, emb_type='fasttext',
                 length_type='mean', dense_units=128):
        """Init function for the model.
        """
        super(CNNRNNModel, self).__init__(max_len=max_len, path_train=path_train,
                                          path_test=path_test, path_dev=path_dev, batch_size=batch_size,
                                          embedding_size=embedding_size, emb_type=emb_type, vocab_size=vocab_size,
                                          max_sequence_len=max_sequence_len, epochs=epochs, learning_rate=learning_rate,
                                          optimizer=optimizer, load_embeddings=load_embeddings, rate=rate,
                                          length_type=length_type, dense_units=dense_units)
        self.filters = filters
        self.kernel_size = kernel_size
        self.pool_size = pool_size
        self.lstm_units = lstm_units
        self.buffer_size = buffer_size
        self.callbacks = None
        self.checkpoint_filepath = './checkpoints/checkpoint_bilstm.cpk'
        self.model_save = ModelCheckpoint(filepath=self.checkpoint_filepath, save_weights_only=True, mode='max',
                                          monitor='val_accuracy', save_best_only=True)
        self.reduce_lr = ReduceLROnPlateau(monitor='val_loss', patience=2, factor=0.2, verbose=0, mode='auto',
                                           min_lr=(self.learning_rate / 100))
        self.early_stop = tf.keras.callbacks.EarlyStopping(
            monitor='val_loss', patience=5, verbose=1, mode='min',
            baseline=None, restore_best_weights=False
        )
        self.callbacks = [self.model_save, self.early_stop]
        # self.callbacks = None

    def call(self):
        """Build the model with all the layers.
        The idea is to build a CNN-RNN model. With de Conv1D layer I try to focus the attention from the model to
        the most important words from the sequence. MaxPooling is used for better performance.
        Then I use 2 BLSTM layers to learn better the information from the data. I apply Dropout to prevent overfitting.
        Arguments:
            - input_shape: Added but not need to use cause max_sequence_len is used.
        """
        # Prepraring the embeddings input
        sequence_input = tf.keras.layers.Input(shape=(self.max_sequence_len,), dtype="int32", name="seq_input")
        embedding_layer = tf.keras.layers.Embedding(self.nb_words, self.embedding_size,
                                                    weights=[self.embeddings_matrix],
                                                    input_length=self.max_sequence_len,
                                                    trainable=False, name='embeddings')
        embedding_sequence = embedding_layer(sequence_input)

        # Add the BiLSTM layer
        x = Bidirectional(LSTM(units=self.lstm_units, activation='tanh', return_sequences=True,
                               recurrent_dropout=0, recurrent_activation='sigmoid', unroll=False, use_bias=True,
                               kernel_regularizer=l2(0.0001)), name='bilstm')(embedding_sequence)
        # Add the Dense layer
        dense = Dense(units=self.dense_units, activation='relu', kernel_regularizer=l2(0.0001), name='dense_layer')(x)
        max_pooling = GlobalMaxPool1D(name='pooling')(dense)
        # Pred layer
        prediction = Dense(units=2, activation='softmax', name='pred_layer')(max_pooling)
        # For correct metrics precision and recall -> also change train_y, test_y, dev_y to 1D np.array
        # prediction = Dense(units=1, activation='sigmoid', name='pred_layer')(max_pooling)
        # Generate the model
        self.model = Model(inputs=[sequence_input], outputs=[prediction])
        self.model.compile(loss=BinaryCrossentropy(),
                           optimizer=self.optimizer,
                           metrics=self.METRICS)

        self.model.summary()
        # tf.keras.utils.plot_model(self.model, show_shapes=True, dpi=48, to_file='cnnrnnmodel.png')

"""
# Last model done.
self.model.add(
        tf.keras.layers.Embedding(self.nb_words, self.embedding_size,
                                  weights=[self.embeddings_matrix], input_length=self.max_sequence_len,
                                  trainable=False))
self.model.add(Bidirectional(LSTM(self.lstm_units, activation='tanh', # return_sequences=True,
                                  recurrent_dropout=0, recurrent_activation='sigmoid',
                                  unroll=False, use_bias=True,
                                  kernel_regularizer=l2(0.0001))))
self.model.add(Dense(self.dense_units, activation='relu', kernel_regularizer=l2(0.0001)))
self.model.add(Dropout(self.rate))
self.model.add(Dense(2, activation='softmax'))  # bias_initializer=self.initial_bias
"""
