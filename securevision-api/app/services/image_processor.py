import cv2
import numpy as np
from multiprocessing import Pool, cpu_count

from app.services.utils import (
    generate_pob_image_shares, generate_recovery_watermark, receiver_extraction,
    generate_tent_map_random_numbers, generate_detection_watermark, generate_embedded_shares)


def process_channel_encryption(channel_data):
    """
    Process a single color channel with all required operations

    Args:
        channel_data (tuple): Contains (channel_array, channel_name)

    Returns:
        tuple: Processed data for the channel (ES1, ES2, R3, R4)
    """
    channel_array, channel_name, recovery_sequence_1, recovery_sequence_2 = channel_data

    # Perform all operations for this channel
    [R1, R2, S1, S2] = generate_pob_image_shares(channel_array)
    DW1 = generate_detection_watermark(S1)
    DW2 = generate_detection_watermark(S2)
    [RW1, RW2] = generate_recovery_watermark(channel_array, recovery_sequence_1, recovery_sequence_2)
    [ES1, ES2, R3, R4] = generate_embedded_shares(S1, S2, R1, R2, DW1, DW2, RW1, RW2)

    print("----")
    print(channel_name)
    print(R3.shape, R4.shape)
    print("----")
    return ES1, ES2, R3, R4, channel_name


def encrypt_image(img, num_processes=None):
    """
    Encrypts an image using parallel processing and returns two shares

    Args:
        image_path (str): Path to the input image
        num_processes (int, optional): Number of processes to use. Defaults to None (uses CPU count)

    Returns:
        tuple: (share1, share2, recovery_data) - Two encrypted shares and recovery data
    """

    # Split into BGR channels
    b, g, r = cv2.split(img)

    recovery_sequence_1 = generate_tent_map_random_numbers(pow(10, -5))
    recovery_sequence_2 = generate_tent_map_random_numbers(pow(10, -8))

    # Prepare channel data for parallel processing
    channel_data = [
        (b, 'blue', recovery_sequence_1, recovery_sequence_2),
        (g, 'green', recovery_sequence_1, recovery_sequence_2),
        (r, 'red', recovery_sequence_1, recovery_sequence_2)
    ]

    # Set up the process pool
    if num_processes is None:
        num_processes = min(cpu_count(), 3)  # Use at most 3 processes

    # Process channels in parallel
    with Pool(processes=num_processes) as pool:
        results = pool.map(process_channel_encryption, channel_data)

    # Organize results
    ES1_channels = []
    ES2_channels = []
    recovery_data = {}

    for ES1, ES2, R3, R4, channel_name in results:
        ES1_channels.append(ES1)
        ES2_channels.append(ES2)
        recovery_data[channel_name] = (R3, R4)

    # Merge channels for final shares
    share1 = cv2.merge(ES1_channels)
    share2 = cv2.merge(ES2_channels)

    return share1, share2, recovery_data


def process_channel_decryption(args):
    """
    Process a single color channel for decryption

    Args:
        args (tuple): Contains (ES1, ES2, R3, R4, channel_name)

    Returns:
        tuple: (extracted_channel, channel_name)
    """
    ES1, ES2, R3, R4, channel_name = args
    [_, _, _, _, _, _, RS3, RS4] = receiver_extraction(ES1, ES2, R3, R4)
    extracted_channel = np.bitwise_xor(RS3, RS4).astype(np.uint8)
    return channel_name, extracted_channel  # Switched order to put string first


def decrypt_image(share1, share2, recovery_data):
    """
    Decrypts two shares back into the original image using parallel processing

    Args:
        share1 (numpy.ndarray): First encrypted share
        share2 (numpy.ndarray): Second encrypted share
        recovery_data (dict): Recovery data from encryption

    Returns:
        numpy.ndarray: Decrypted image
    """
    # Split shares into channels
    ES1b, ES1g, ES1r = cv2.split(share1)
    ES2b, ES2g, ES2r = cv2.split(share2)

    # Prepare channel data for parallel processing
    channel_data = [
        (ES1b, ES2b, *recovery_data['blue'], 'blue'),
        (ES1g, ES2g, *recovery_data['green'], 'green'),
        (ES1r, ES2r, *recovery_data['red'], 'red')
    ]

    # Process channels in parallel using all available cores (up to 3)
    with Pool(processes=min(cpu_count(), 3)) as pool:
        results = pool.map(process_channel_decryption, channel_data)

    # Create lists to store channels in correct order
    channels = []
    for channel_name, extracted_channel in sorted(results):  # Sort by channel name to ensure correct order
        if channel_name == 'blue':
            channels.append(extracted_channel)
        elif channel_name == 'green':
            channels.append(extracted_channel)
        elif channel_name == 'red':
            channels.append(extracted_channel)

    # Merge channels for final image
    recovered_img = cv2.merge(channels)

    return recovered_img
