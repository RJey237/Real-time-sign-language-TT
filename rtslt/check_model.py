from tensorflow import keras
m = keras.models.load_model('ml_models/saved_models/lstm_model.h5')
print('Input shape:', m.input_shape)
print('\nModel Summary:')
m.summary()
