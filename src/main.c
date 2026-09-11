/*
 * GBA starter program.
 *
 * Boots into bitmap mode 3 (240x160, one u16 BGR555 pixel per pixel),
 * draws a gradient background and lets you move an 8x8 square with the
 * D-pad. Press A to change the square's color.
 *
 * Build with `make`, then run with `make run` (opens mGBA).
 */

typedef unsigned char  u8;
typedef unsigned short u16;
typedef unsigned int   u32;

#define MEM_IO   0x04000000u
#define MEM_VRAM 0x06000000u

#define REG_DISPCONTROL (*(volatile u16 *)(MEM_IO + 0x000))
#define REG_VCOUNT      (*(volatile u16 *)(MEM_IO + 0x002))
#define REG_KEYINPUT    (*(volatile u16 *)(MEM_IO + 0x130))

#define SCREEN_WIDTH  240
#define SCREEN_HEIGHT 160

/* Display control bits */
#define DCNT_MODE3 0x0003 /* bitmap mode 3 */
#define DCNT_BG2   0x0400 /* enable BG layer 2 */

/* Key bits: 0 = pressed in REG_KEYINPUT */
#define KEY_A      0x0001
#define KEY_B      0x0002
#define KEY_SELECT 0x0004
#define KEY_START  0x0008
#define KEY_RIGHT  0x0010
#define KEY_LEFT   0x0020
#define KEY_UP     0x0040
#define KEY_DOWN   0x0080

/* 15-bit BGR color, channels 0..31 */
#define RGB15(r, g, b) ((u16)((r) | ((g) << 5) | ((b) << 10)))

static u16 *const vram = (u16 *)MEM_VRAM;

/* Block until the start of vblank; all drawing after this is flicker-free. */
static void vsync(void)
{
    while (REG_VCOUNT >= SCREEN_HEIGHT) {
    }
    while (REG_VCOUNT < SCREEN_HEIGHT) {
    }
}

static void plot(int x, int y, u16 color)
{
    vram[y * SCREEN_WIDTH + x] = color;
}

static void fill_rect(int x, int y, int w, int h, u16 color)
{
    for (int row = 0; row < h; row++) {
        for (int col = 0; col < w; col++) {
            plot(x + col, y + row, color);
        }
    }
}

/* Background is a vertical gradient; row_color is reused to erase sprites. */
static u16 row_color(int y)
{
    return RGB15(2 + (y >> 4), 4 + (y >> 3), 16 - (y >> 4));
}

static void draw_background(void)
{
    for (int y = 0; y < SCREEN_HEIGHT; y++) {
        u16 color = row_color(y);
        for (int x = 0; x < SCREEN_WIDTH; x++) {
            plot(x, y, color);
        }
    }
}

int main(void)
{
    static const u16 colors[] = {
        RGB15(31, 31, 31), /* white  */
        RGB15(31, 22, 0),  /* yellow */
        RGB15(0, 31, 31),  /* cyan   */
        RGB15(31, 5, 5),   /* red    */
        RGB15(10, 31, 5),  /* green  */
    };
    const int num_colors = (int)(sizeof(colors) / sizeof(colors[0]));

    REG_DISPCONTROL = DCNT_MODE3 | DCNT_BG2;
    draw_background();

    const int size = 8;
    const int speed = 2;
    int px = SCREEN_WIDTH / 2 - size / 2;
    int py = SCREEN_HEIGHT / 2 - size / 2;
    int color_index = 0;
    u16 prev_keys = 0;

    while (1) {
        vsync();

        u16 keys = (u16)(~REG_KEYINPUT & 0x03FF); /* 1 = pressed */

        int dx = 0;
        int dy = 0;
        if (keys & KEY_LEFT)  dx -= speed;
        if (keys & KEY_RIGHT) dx += speed;
        if (keys & KEY_UP)    dy -= speed;
        if (keys & KEY_DOWN)  dy += speed;

        if ((keys & KEY_A) && !(prev_keys & KEY_A)) {
            color_index = (color_index + 1) % num_colors;
        }
        prev_keys = keys;

        /* Erase old square with the gradient colors it covers. */
        for (int row = 0; row < size; row++) {
            fill_rect(px, py + row, size, 1, row_color(py + row));
        }

        px += dx;
        py += dy;
        if (px < 0) px = 0;
        if (py < 0) py = 0;
        if (px > SCREEN_WIDTH - size) px = SCREEN_WIDTH - size;
        if (py > SCREEN_HEIGHT - size) py = SCREEN_HEIGHT - size;

        fill_rect(px, py, size, size, colors[color_index]);
    }
}
