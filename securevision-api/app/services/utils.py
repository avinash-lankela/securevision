import copy as c
import numpy as np
from scipy.special import comb

def calculate_pob_value(binary_array):
    """
    Calculate POB (Position-Ordered Binary) value for a binary array

    Args:
        binary_array: numpy array of binary digits (0s and 1s)

    Returns:
        int: POB value
    """
    # Reverse the array for position calculation
    reversed_array = binary_array[::-1]

    # Find positions of 1s
    one_positions = np.where(reversed_array == 1)[0]
    # Exclude first position as per original logic
    one_positions = one_positions[one_positions > 0]

    if len(one_positions) == 0:
        return 0

    # Calculate cumulative sum
    cumsum = np.cumsum(reversed_array)

    # Calculate combinations for each valid position
    result = 0
    for pos in one_positions:
        result += comb(int(pos), int(cumsum[pos]), exact=True)

    return result

def generate_pob_image_shares(image):
    """
    Generate shares for an input image using POB scheme

    Args:
        image: 2D numpy array representing the input image

    Returns:
        tuple: (r1, r2, share_1, share_2) arrays reshaped to original image dimensions
    """
    # Store original dimensions
    original_shape = image.shape

    # Flatten image and generate binary representation
    flat_image = image.flatten()
    binary_arrays = ((flat_image[:,None] & (1 << np.arange(7,-1,-1))) > 0).astype(int)

    # Initialize arrays
    total_pixels = len(flat_image)
    a = np.zeros_like(binary_arrays)

    # Handle zero positions with random values
    zero_positions = (binary_arrays == 0)
    a[zero_positions] = np.random.choice([0, 1], size=np.sum(zero_positions))

    # Handle one positions based on cumulative sum
    one_positions = (binary_arrays == 1)
    cumsum = np.cumsum(binary_arrays, axis=1)
    a[one_positions] = (cumsum[one_positions] % 2 == 0)

    # Generate random array and perform XOR operations
    r = np.random.choice([0, 1], size=(total_pixels, 8))
    a = np.bitwise_xor(a, r)
    b = np.bitwise_xor(a, binary_arrays)

    # Calculate sums for r1 and r2
    r1 = np.sum(a, axis=1).reshape(original_shape)
    r2 = np.sum(b, axis=1).reshape(original_shape)

    # Calculate shares using POB
    share_1 = np.array([calculate_pob_value(arr) for arr in a]).reshape(original_shape)
    share_2 = np.array([calculate_pob_value(arr) for arr in b]).reshape(original_shape)

    return r1, r2, share_1, share_2

def generate_detection_watermark(share_array):
    """
    Generate detection watermark from input share array.

    Parameters:
    share_array: numpy array of shape (height, width)

    Returns:
    watermark_bits: numpy array containing three watermark bits for each 2x2 block
    """
    # Convert input array into 2x2 blocks
    height, width = share_array.shape
    blocks = share_array.reshape(height//2, 2, width//2, 2).transpose(0, 2, 1, 3).reshape(-1, 2, 2)

    # Get singular values for all blocks (only s values needed)
    s = np.linalg.svd(blocks, compute_uv=False)

    # Calculate delta and eta for all blocks
    delta = s[:, 0] - s[:, 1]
    eta = s[:, 0] + s[:, 1]

    # Calculate wd1 (parity bits from delta)
    is_whole_delta = (delta % 1) == 0
    epsilon_values = np.where(is_whole_delta,
                            delta,
                            (delta - np.floor(delta)) * (10 ** len(str((delta - np.floor(delta))[0])[2:])))
    wd1 = np.array([bin(int(x)).count('1') % 2 for x in epsilon_values])

    # Calculate wd2 (threshold check on delta)
    wd2 = (delta >= 255).astype(int)

    # Calculate wd3 (parity bits from eta)
    is_whole_eta = (eta % 1) == 0
    neta_values = np.where(is_whole_eta,
                          eta,
                          (eta - np.floor(eta)) * (10 ** len(str((eta - np.floor(eta))[0])[2:])))
    wd3 = np.array([bin(int(x)).count('1') % 2 for x in neta_values])

    # Stack all watermark bits together
    # Reshape to match original output format (length, 1, 3)
    watermark_bits = np.column_stack((wd1, wd2, wd3)).reshape(-1, 1, 3)

    return watermark_bits

def generate_tent_map_random_numbers(seed):
    """
    Generates an array of unique random numbers based on the tent map algorithm.

    Parameters:
    - seed (float): A starting value for the tent map, typically a small number
      (e.g., 10^-5 or 10^-8), which determines the sequence.

    Returns:
    - np.ndarray: A NumPy array containing 16384 unique random numbers
      ranging from 0 to 16383.
    """
    # Initialize the array with -1 to represent unused slots
    unique_numbers = np.full(16384, -1, dtype=int)
    # Boolean mask to track already used numbers
    number_present = np.zeros(16384, dtype=bool)
    # Index to track the next insertion point
    insert_index = 0

    # Generate random numbers until the array is filled
    while insert_index < 16384:
        # Update seed using the tent map formula
        if seed < 0.5:
            seed = seed * 1.999999
        else:
            seed = (1 - seed) * 1.999999

        # Generate a random number in the range [0, 16383]
        random_number = round((seed * 10**14) % 16383)

        # Add the number if it is not already present
        if not number_present[random_number]:
            unique_numbers[insert_index] = random_number
            number_present[random_number] = True
            insert_index += 1

    return unique_numbers

def generate_recovery_watermark(image, indices_sequence_1, indices_sequence_2):
    blocks = image.reshape(256//2, 2, 256//2, 2).transpose(0, 2, 1, 3).reshape(-1, 2, 2)

    # Ensure integer type for block means
    block_means = (blocks.sum(axis=(1,2)) // 4).astype(np.uint8)

    recovery_watermark = np.zeros([16384, 1, 5], dtype=np.uint8)
    for idx in range(16384):
        bin_val = bin(block_means[idx]).lstrip("0b").zfill(5)
        recovery_watermark[idx] = [bin_val[0], bin_val[1], bin_val[2], bin_val[3], bin_val[4]]

    recovery_watermark_1 = recovery_watermark[indices_sequence_1, :, :]
    recovery_watermark_2 = recovery_watermark[indices_sequence_2, :, :]

    return recovery_watermark_1, recovery_watermark_2

def pob(n, r, v):
    B = np.zeros([n], dtype=np.uint8)
    t = r
    temp = v
    for i in range(n - 1, 0, -1):
        x = comb(i, t, exact=True)
        if x <= temp:
            temp -= x
            t -= 1
            B[i] = 1
    if t != 0:
        B[0] = 1
    return B[::-1]

def generate_embedded_shares(
        pob_share_1, pob_share_2,
        rand_num_seq_1, rand_num_seq_2,
        detection_watermark_1, detection_watermark_2,
        recovery_watermark_1, recovery_watermark_2
):
    """
    Generate embedded shares from POB shares and watermarks.
    """
    height, width = pob_share_1.shape

    # Convert shares and random sequences into 2x2 blocks
    pob_share_1_blocks = pob_share_1.reshape(height // 2, 2, width // 2, 2).transpose(0, 2, 1, 3).reshape(-1, 2, 2)
    pob_share_2_blocks = pob_share_2.reshape(height // 2, 2, width // 2, 2).transpose(0, 2, 1, 3).reshape(-1, 2, 2)
    rand_seq_1_blocks = rand_num_seq_1.reshape(height // 2, 2, width // 2, 2).transpose(0, 2, 1, 3).reshape(-1, 2, 2)
    rand_seq_2_blocks = rand_num_seq_2.reshape(height // 2, 2, width // 2, 2).transpose(0, 2, 1, 3).reshape(-1, 2, 2)

    # Initialize arrays for storing extended binary patterns
    extended_arrays_1 = np.zeros((16384, 4, 10), dtype=np.uint8)
    extended_arrays_2 = np.zeros((16384, 4, 10), dtype=np.uint8)

    # Generate binary arrays using current pob function
    for i in range(16384):
        # For share 1
        extended_arrays_1[i, 0, :8] = pob(8, rand_seq_1_blocks[i, 0, 0], pob_share_1_blocks[i, 0, 0])
        extended_arrays_1[i, 1, :8] = pob(8, rand_seq_1_blocks[i, 0, 1], pob_share_1_blocks[i, 0, 1])
        extended_arrays_1[i, 2, :8] = pob(8, rand_seq_1_blocks[i, 1, 0], pob_share_1_blocks[i, 1, 0])
        extended_arrays_1[i, 3, :8] = pob(8, rand_seq_1_blocks[i, 1, 1], pob_share_1_blocks[i, 1, 1])

        # For share 2
        extended_arrays_2[i, 0, :8] = pob(8, rand_seq_2_blocks[i, 0, 0], pob_share_2_blocks[i, 0, 0])
        extended_arrays_2[i, 1, :8] = pob(8, rand_seq_2_blocks[i, 0, 1], pob_share_2_blocks[i, 0, 1])
        extended_arrays_2[i, 2, :8] = pob(8, rand_seq_2_blocks[i, 1, 0], pob_share_2_blocks[i, 1, 0])
        extended_arrays_2[i, 3, :8] = pob(8, rand_seq_2_blocks[i, 1, 1], pob_share_2_blocks[i, 1, 1])

    # Add watermark bits
    # For share 1
    extended_arrays_1[:, 0, 8:10] = detection_watermark_1[:, 0, :2]
    extended_arrays_1[:, 1, 8] = detection_watermark_1[:, 0, 2]
    extended_arrays_1[:, 1, 9] = recovery_watermark_1[:, 0, 0]
    extended_arrays_1[:, 2, 8:10] = recovery_watermark_1[:, 0, 1:3]
    extended_arrays_1[:, 3, 8:10] = recovery_watermark_1[:, 0, 3:5]

    # For share 2
    extended_arrays_2[:, 0, 8:10] = detection_watermark_2[:, 0, :2]
    extended_arrays_2[:, 1, 8] = detection_watermark_2[:, 0, 2]
    extended_arrays_2[:, 1, 9] = recovery_watermark_2[:, 0, 0]
    extended_arrays_2[:, 2, 8:10] = recovery_watermark_2[:, 0, 1:3]
    extended_arrays_2[:, 3, 8:10] = recovery_watermark_2[:, 0, 3:5]

    # Calculate POB values and sums
    # Shape of results will be (16384, 4) as we're operating on each 10-bit sequence
    pob_share_result_1 = np.array([calculate_pob_value(arr) for arr in extended_arrays_1.reshape(-1, 10)]).reshape(
        16384, 4)
    pob_share_result_2 = np.array([calculate_pob_value(arr) for arr in extended_arrays_2.reshape(-1, 10)]).reshape(
        16384, 4)

    sum_share_result_1 = np.sum(extended_arrays_1, axis=2)  # Shape: (16384, 4)
    sum_share_result_2 = np.sum(extended_arrays_2, axis=2)  # Shape: (16384, 4)

    # Need to reshape back to (16384, 2, 2) before final block 2 arr
    pob_share_result_1 = pob_share_result_1.reshape(16384, 2, 2)
    pob_share_result_2 = pob_share_result_2.reshape(16384, 2, 2)
    sum_share_result_1 = sum_share_result_1.reshape(16384, 2, 2)
    sum_share_result_2 = sum_share_result_2.reshape(16384, 2, 2)

    # Convert back to original image shape - Convert (16384, 2, 2) back to (256, 256)
    embedded_share_1 = pob_share_result_1.reshape(height // 2, width // 2, 2, 2).transpose(0, 2, 1, 3).reshape(height,
                                                                                                               width)
    embedded_share_2 = pob_share_result_2.reshape(height // 2, width // 2, 2, 2).transpose(0, 2, 1, 3).reshape(height,
                                                                                                               width)
    share_sum_1 = sum_share_result_1.reshape(height // 2, width // 2, 2, 2).transpose(0, 2, 1, 3).reshape(height, width)
    share_sum_2 = sum_share_result_2.reshape(height // 2, width // 2, 2, 2).transpose(0, 2, 1, 3).reshape(height, width)

    return [embedded_share_1, embedded_share_2, share_sum_1, share_sum_2]


def fun(x):
    return c.deepcopy(x)

def dec_num(arr):
    p = 0
    for i in range(len(arr)):
        k = len(arr) - i - 1
        p += arr[i] * (2 ** k)
    return p

def arr2blocks(arr, nrows, ncols):
    h, w = arr.shape
    return arr.reshape(h // nrows, nrows, -1, ncols).swapaxes(1, 2).reshape(-1, nrows, ncols)

def blocks2arr(arr, h, w):
    n, nrows, ncols = arr.shape
    return arr.reshape(h // nrows, -1, nrows, ncols).swapaxes(1, 2).reshape(h, w)

def receiver_extraction(es1, es2, r11, r22):
    a1 = arr2blocks(es1, 2, 2)
    a2 = arr2blocks(es2, 2, 2)
    a3 = arr2blocks(r11, 2, 2)
    a4 = arr2blocks(r22, 2, 2)
    s1 = np.zeros([16384, 2, 2], dtype=np.uint8)
    s2 = np.zeros([16384, 2, 2], dtype=np.uint8)
    s3 = np.zeros([16384, 2, 2], dtype=np.uint8)
    s4 = np.zeros([16384, 2, 2], dtype=np.uint8)
    dw1 = np.zeros([16384, 1, 3], dtype=np.uint8)
    dw2 = np.zeros([16384, 1, 3], dtype=np.uint8)
    dr1 = np.zeros([16384, 1, 5], dtype=np.uint8)
    dr2 = np.zeros([16384, 1, 5], dtype=np.uint8)
    for i in range(16384):
        x = a1[i]
        e1 = x[0][0]
        e2 = x[0][1]
        e3 = x[1][0]
        e4 = x[1][1]
        y = a3[i]
        r1 = y[0][0]
        r2 = y[0][1]
        r3 = y[1][0]
        r4 = y[1][1]
        pe1 = pob(10, r1, e1)
        pe2 = pob(10, r2, e2)
        pe3 = pob(10, r3, e3)
        pe4 = pob(10, r4, e4)
        s1[i] = [[calculate_pob_value(pe1[0:8]), calculate_pob_value(pe2[0:8])], [calculate_pob_value(pe3[0:8]), calculate_pob_value(pe4[0:8])]]
        s3[i] = [[dec_num(pe1[0:8]), dec_num(pe2[0:8])], [dec_num(pe3[0:8]), dec_num(pe4[0:8])]]
        dw1[i] = [[pe1[8], pe1[9], pe2[8]]]
        dr1[i] = [[pe2[9], pe3[8], pe3[9], pe4[8], pe4[9]]]
        x = a2[i]
        e1 = x[0][0]
        e2 = x[0][1]
        e3 = x[1][0]
        e4 = x[1][1]
        y = a4[i]
        r1 = y[0][0]
        r2 = y[0][1]
        r3 = y[1][0]
        r4 = y[1][1]
        pe1 = pob(10, r1, e1)
        pe2 = pob(10, r2, e2)
        pe3 = pob(10, r3, e3)
        pe4 = pob(10, r4, e4)
        s2[i] = [[calculate_pob_value(pe1[0:8]), calculate_pob_value(pe2[0:8])], [calculate_pob_value(pe3[0:8]), calculate_pob_value(pe4[0:8])]]
        s4[i] = [[dec_num(pe1[0:8]), dec_num(pe2[0:8])], [dec_num(pe3[0:8]), dec_num(pe4[0:8])]]
        dw2[i] = [[pe1[8], pe1[9], pe2[8]]]
        dr2[i] = [[pe2[9], pe3[8], pe3[9], pe4[8], pe4[9]]]
    share1 = blocks2arr(s1, 256, 256)
    share2 = blocks2arr(s2, 256, 256)
    share3 = blocks2arr(s3, 256, 256)
    share4 = blocks2arr(s4, 256, 256)
    return [share1, share2, dw1, dw2, dr1, dr2, share3, share4]

def check_detection_watermark(dw, rdw):
    blocks_tampered = []
    count11 = 0
    for i in range(16384):
        if dw[i].all() != rdw[i].all():
            blocks_tampered.append(i)
            count11 += 1
    return [count11, blocks_tampered]

def recovery_watermark_extraction(rw1, rw2):
    t1 = generate_tent_map_random_numbers(pow(10, -5))
    t2 = generate_tent_map_random_numbers(pow(10, -8))
    rw11 = np.zeros([16384, 1, 5], dtype=np.uint8)
    rw22 = np.zeros([16384, 1, 5], dtype=np.uint8)
    for i in range(16384):
        rw11[t1[i]] = rw1[i]
        rw22[t2[i]] = rw2[i]
    return [rw11, rw22]
