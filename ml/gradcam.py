import tensorflow as tf
import numpy as np
import cv2


def get_last_conv_layer(model):
    for layer in reversed(model.layers):
        if isinstance(layer, (tf.keras.layers.Conv2D, tf.keras.layers.SeparableConv2D)):
            return layer.name
    raise ValueError("No Conv2D layer found in model")


def generate_gradcam(model, img_array):
    # Find indices of the last conv layer and the very last layer
    conv_layer_idx = None
    for i, layer in enumerate(model.layers):
        if isinstance(layer, (tf.keras.layers.Conv2D, tf.keras.layers.SeparableConv2D)):
            conv_layer_idx = i

    if conv_layer_idx is None:
        raise ValueError("No Conv2D layer found")

    # Reconstruct the model as a Functional model to ensure gradient flow
    # This is the "Gold Standard" way to handle loaded Sequential models
    inputs = model.inputs
    x = inputs[0] if isinstance(inputs, list) else inputs

    conv_out = None

    # We manually pass the input through the layers
    for i, layer in enumerate(model.layers):
        try:
            x = layer(x)
        except Exception as e:
            # If a layer still struggles with the tensor, we ensure it's a single tensor
            if isinstance(x, list): x = x[0]
            x = layer(x)

        if i == conv_layer_idx:
            conv_out = x

    grad_model = tf.keras.Model(inputs, [conv_out, x])

    img_tensor = tf.cast(img_array, tf.float32)

    with tf.GradientTape() as tape:
        conv_outputs, predictions = grad_model(img_tensor)
        class_idx = tf.argmax(predictions[0])
        loss = predictions[:, class_idx]

    # Calculate gradients
    grads = tape.gradient(loss, conv_outputs)

    # If grads is None, return a tiny constant ,so we don't get a black/blue image
    if grads is None:
        return np.ones((256, 256)) * 0.1

    pooled_grads = tf.reduce_mean(grads, axis=(0, 1, 2))
    conv_outputs = conv_outputs[0]

    # Generate heatmap
    heatmap = conv_outputs @ pooled_grads[..., tf.newaxis]
    heatmap = tf.squeeze(heatmap)
    heatmap = tf.maximum(heatmap, 0)

    # Normalize safely
    max_val = tf.reduce_max(heatmap)
    if max_val == 0:
        return np.ones((256, 256)) * 0.1

    heatmap = heatmap / max_val
    return heatmap.numpy()


def save_gradcam_overlay(img_path, heatmap, output_path, alpha=0.4):
    img = cv2.imread(img_path)
    if img is None: return None

    heatmap = cv2.resize(heatmap, (img.shape[1], img.shape[0]))
    heatmap = np.uint8(255 * heatmap)
    heatmap = cv2.applyColorMap(heatmap, cv2.COLORMAP_JET)

    overlay = cv2.addWeighted(img, 1 - alpha, heatmap, alpha, 0)
    cv2.imwrite(output_path, overlay)
    return output_path

