/*
 * Freestanding libc basics.
 *
 * The game links with -nostdlib, but GCC may still emit calls to
 * memcpy/memset for struct copies and block initialization (struct
 * assignment in C counts as a block copy), so tiny implementations live
 * here. The host test builds compile src/main.c directly against the real
 * libc and never see this file.
 */

void *memcpy(void *dst, const void *src, unsigned int n)
{
    unsigned char *d = dst;
    const unsigned char *s = src;
    while (n--)
        *d++ = *s++;
    return dst;
}

void *memset(void *dst, int value, unsigned int n)
{
    unsigned char *d = dst;
    while (n--)
        *d++ = (unsigned char)value;
    return dst;
}

void *memmove(void *dst, const void *src, unsigned int n)
{
    unsigned char *d = dst;
    const unsigned char *s = src;
    if (d < s) {
        while (n--)
            *d++ = *s++;
    } else if (d > s) {
        d += n;
        s += n;
        while (n--)
            *--d = *--s;
    }
    return dst;
}
