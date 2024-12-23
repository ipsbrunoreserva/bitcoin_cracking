#include "./kernel/bip39.cl"

void pbkdf2_hmac_sha512_long(ulong *password, uchar password_len, ulong *T);
uchar sha256_from_byte(ulong max, ulong min);

#define CONCAT_BLOCK(b)                                                        \
  {                                                                            \
    ulong val = 0UL;                                                           \
    for (int i = 0; i < 8; i++) {                                              \
      val |= ((ulong)seedString[(b) * 8 + i]) << (8 * i);                      \
    }                                                                          \
    blocks[(b)] = val;                                                         \
  }

#define CONCAT_WORD(w)                                                         \
  {                                                                            \
    int wIdx = seedNum[(w)];                                                   \
    for (int i = 0; i < 9; ++i) {                                              \
      seedString[offset + i] = wordsString[wIdx][i];                           \
    }                                                                          \
    offset += wordsLen[wIdx] + 1;                                              \
  }

__kernel void pbkdf2_hmac_sha512_test(__global uchar *py,
                                      __global uchar *input) {

  ulong mnemonic_long[32];
  ulong aa[8];
  uchar result[128];
  uchar_to_ulong(input, strlen(input), mnemonic_long, 0);
  INIT_SHA512(aa);
  pbkdf2_hmac_sha512_long(mnemonic_long, strlen(input), aa);
  ulong_array_to_char(aa, 8, result);

  if (strcmp(result, py)) {
    printf("\niguais");
  } else {
    printf("\ndiferentes\n");
    printf("Veio de la: %s %s %s\n", input, result, py);
  }
}

__kernel void verifySeed(__global ulong *output, ulong O, ulong H, ulong L,
                         ulong V) {
  int gid = get_global_id(0);
  int total_work_items = get_global_size(0);
  ulong memHigh = H;
  ulong memLow = L + (O + gid) * V;
  ulong finalMem = memLow + V;

  uint seedNum[12] = {0};
  seedNum[0] = (memHigh & (2047UL << 53UL)) >> 53UL;
  seedNum[1] = (memHigh & (2047UL << 42UL)) >> 42UL;
  seedNum[2] = (memHigh & (2047UL << 31UL)) >> 31UL;
  seedNum[3] = (memHigh & (2047UL << 20UL)) >> 20UL;
  seedNum[4] = (memHigh & (2047UL << 9UL)) >> 9UL;
  seedNum[5] = (memHigh << 55UL) >> 53UL | ((memLow & (3UL << 62UL)) >> 62UL);
  seedNum[6] = (memLow & (2047UL << 51UL)) >> 51UL;

  uint offset = 0;
  uchar seedString[128] = {0};
  ulong blocks[16] = {0};

  CONCAT_WORD(0);
  CONCAT_WORD(1);
  CONCAT_WORD(2);
  CONCAT_WORD(3);
  CONCAT_WORD(4);
  CONCAT_WORD(5);
  CONCAT_WORD(6);
  uint oldOffset = offset;
  uint fixBlock = offset / 8;

#pragma unroll 9
  for (int i = 0; i < fixBlock; i++) {
    CONCAT_BLOCK(i);
  }
  ulong mnemonic_long[16] = {0};
  uchar_to_ulong(seedString, offset, mnemonic_long, 0);

  for (; memLow < finalMem; memLow++) {
    uchar checksum = sha256_from_byte(memHigh, memLow) >> 4UL;
    seedNum[7] = (memLow & (2047UL << 40UL)) >> 40UL;
    seedNum[8] = (memLow & (2047UL << 29UL)) >> 29UL;
    seedNum[9] = (memLow & (2047UL << 18UL)) >> 18UL;
    seedNum[10] = (memLow & (2047UL << 7UL)) >> 7UL;
    seedNum[11] = ((memLow << 57UL) >> 53UL) | checksum;

    CONCAT_WORD(7);
    CONCAT_WORD(8);
    CONCAT_WORD(9);
    CONCAT_WORD(10);
    CONCAT_WORD(11);

    seedString[offset - 1] = '\0';

#pragma unroll
    for (int i = fixBlock; i < 16; i++) {
      CONCAT_BLOCK(i);
    }

    ulong pbkdf2_long[8] = {0};
    uchar result[128] = {0};
    uchar_to_ulong(seedString, offset - 1, mnemonic_long, fixBlock);
    ////////////////////////

    pbkdf2_hmac_sha512_long(mnemonic_long, offset - 1, pbkdf2_long);

    if (memLow % 10000000 == 0) {
      ulong_array_to_char(pbkdf2_long, 8, result);
      printf("\nSeed: |%s|%s|\n", seedString, result);
    }

    offset = oldOffset;
  }
}
