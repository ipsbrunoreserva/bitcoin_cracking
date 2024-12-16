import numpy as np
import pyopencl as cl
from mnemonic import Mnemonic

import time


mnemo = Mnemonic("english")




FIXED_WORDS = "leg floor love render render bad abandon abandon abandon abandon abandon abandoon".split()
DESTINY_WALLET = "bc1qrgs8g7hn2qu8f5akjyyu8g7uxvxlpc4z0gupfx"

BATCH_SIZE = 10
LOCAL_WORKERS = 24
WORKERS = LOCAL_WORKERS*1024
print("Analisando: ", FIXED_WORDS)





def main():
    try:
        indices = words_to_indices(FIXED_WORDS)
    except ValueError as e:
        print(f"Error ao converter palavras em índices: {e}")
        return
    context, queue = initialize_opencl()
    if context is None or queue is None:
        print("Erro ao inicializar o OpenCL. Verifique sua instalação ou configuração.")
        return
    print("OpenCL inicializado com sucesso.")
    try:
        program = build_program(context, "./kernel/common.cl",  "./kernel/sha512_hmac.cl", "./kernel/sha256.cl", "./kernel/main.cl")
    except Exception as e:
        print(f"Erro ao compilar o programa OpenCL: {e}")
        return
    
    print("Programa OpenCL compilado com sucesso.")
    try:
        run_kernel(program, queue, indices, BATCH_SIZE)
        print("Kernel executado com sucesso.")
    except Exception as e:
        print(f"Erro durante a execução do kernel: {e}")
def load_program_source(filename):
    with open(filename, 'r') as f:
        return f.read()




        
def initialize_opencl():
    try:
        platform = cl.get_platforms()[0]
        device = platform.get_devices()[0]
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





def mnemonic_to_uint64_pair(indices):
    binary_string = ''.join(f"{index:011b}" for index in indices)[:-4]  
    binary_string = binary_string.ljust(128, '0')
    high = int(binary_string[:64], 2)
    low = int(binary_string[64:], 2)
    return high, low






def run_kernel(program, queue, indices, batch_size):
    context = program.context
    high, low = mnemonic_to_uint64_pair(words_to_indices(FIXED_WORDS))
    indices_buffer = cl.Buffer(context, cl.mem_flags.READ_ONLY | cl.mem_flags.COPY_HOST_PTR, hostbuf=np.array(indices, dtype=np.uint32))
    np64 = cl.Buffer(context, cl.mem_flags.READ_ONLY | cl.mem_flags.COPY_HOST_PTR, hostbuf=np.array([high, low], dtype=np.uint64))
    kernel = program.generate_combinations
    kernel.set_args(indices_buffer, np64, np.uint64(batch_size))
    global_size = (WORKERS,)
    start_time = time.time()
    cl.enqueue_nd_range_kernel(queue, kernel, global_size, (LOCAL_WORKERS,)).wait()
    
    end_time = time.time()
    elapsed_time = end_time - start_time
    seeds = WORKERS * batch_size
    media = seeds / elapsed_time
    
    print(f"Foram criadas {seeds:,} em {elapsed_time:.6f} seconds media {media:.6f} por seg")
    return True




if __name__ == "__main__":
    main()