import numpy as np
import pyopencl as cl
from mnemonic import Mnemonic
import time

import struct
import os
os.environ['PYOPENCL_COMPILER_OUTPUT'] = '1'

mnemo = Mnemonic("english")



platforms = cl.get_platforms()
print(platforms)
devices = platforms[0].get_devices()
print(devices)
device = devices[0]
max_work_item_sizes = device.max_work_item_sizes 
max_work_group_size = device.max_work_group_size

print(f"Device Name: {device.name}")
print(f"Max Work Item Sizes: {max_work_item_sizes}")
print(f"Max Work Group Size: {max_work_group_size}")


FIXED_WORDS = "actual action amused black abandon adjust winter abandon abandon abandon abandon abandon".split()
DESTINY_WALLET = "bc1q9nfphml9vzfs6qxyyfqdve5vrqw62dp26qhalx"
FIXED_SEED = "actual action amused black abandon adjust winter "

OFFSET = 0
LOCAL_WORKERS = (64,)
WORKERS = (512000, )
BATCH_SIZE = 100



def main(): 
    context, queue = initialize_opencl()
    if context is None or queue is None: 
        print("Erro ao inicializar o OpenCL. Verifique sua instalação ou configuração.")
        return
    print("OpenCL inicializado com sucesso.")

    try:
        program = build_program(context,
                                "./kernel/common.cl",
                                 "./kernel/sha256.cl",
                                 "./kernel/sha512_hmac.cl",
                                "./kernel/main.cl"
             )

        run_kernel(program, queue)
        print("Kernel executado com sucesso.")
    except Exception as e:
        print(f"Erro ao compilar o programa OpenCL: {e}")
        return



def load_program_source(filename):
    with open(filename, 'r') as f:
     content = f.read()
    return content



        
def initialize_opencl():
    try:
        context = cl.Context([device])
        queue = cl.CommandQueue(context)
        return context, queue
    except Exception as e:
        print(f"Erro ao inicializar o OpenCL: {e}")
        return None, None





def build_program(context, *filenames):
    source_code = ""
    for filename in filenames:
        source_code += load_program_source(filename) + "\n\n\n"
    return cl.Program(context, source_code).build()





def words_to_indices(words):
    indices = []
    for word in words:
        if word in mnemo.wordlist:
            indices.append(mnemo.wordlist.index(word))
    return np.array(indices, dtype=np.int32)



def string_to_long_array(s):
    s = s.ljust((len(s) + 7) // 8 * 8)
    long_array = [str(struct.unpack('<Q', s[i:i+8].encode('utf-8'))[0]) for i in range(0, len(s), 8)]
    return '{' + ', '.join(long_array) + '}'


def string_to_long_array(s):
    s = s.ljust((len(s) + 7) // 8 * 8)
    return [struct.unpack('<Q', s[i:i+8].encode('utf-8'))[0] for i in range(0, len(s), 8)]

def mnemonic_to_uint64_pair(indices):
    binary_string = ''.join(f"{index:011b}" for index in indices)[:-4] 
    binary_string = binary_string.ljust(128, '0')
    high = int(binary_string[:64], 2)
    low = int(binary_string[64:], 2)
    return high, low


def run_kernel(program, queue):
    data = np.arange(11, dtype=np.int64)
    context = program.context
    kernel = program.verifySeed
    HIGH, LOW = mnemonic_to_uint64_pair(words_to_indices(FIXED_WORDS))
    output_buffer = cl.Buffer(context, cl.mem_flags.WRITE_ONLY, size=data.nbytes)
    kernel.set_args(output_buffer, np.uint64(OFFSET), np.uint64(HIGH), np.uint64(LOW), np.uint64(BATCH_SIZE))
    start_time = time.time()   
    cl.enqueue_nd_range_kernel(queue, kernel, WORKERS, LOCAL_WORKERS).wait()
    end_time = time.time()
    elapsed_time = end_time - start_time +1
    seeds = WORKERS[0] * BATCH_SIZE

    media = seeds / elapsed_time
    print(f"Foram criadas {seeds:,} em {elapsed_time:.6f} seconds media {media:,} por seg")
    return True


if __name__ == "__main__":
    main()
