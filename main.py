import os
import ffmpeg
import sys

from tqdm import tqdm

from concurrent.futures import ThreadPoolExecutor
import concurrent.futures.thread
import threading

SUPPORTED_EXTENSIONS = [
    ".aac",
    ".ac3",
    ".aptx",
    ".aptxhd",
    ".dfpwm",
    ".dts",
    ".eac3",
    ".ec3",
    ".flac",
    ".tco",
    ".rco",
    ".g723_1",
    ".mlp",
    ".mp2",
    ".mp3",
    ".m2a",
    ".mpa",
    ".sbc",
    ".msbc",
    ".thd",
    ".tta",
]

def convert_to_mp3(input_path, output_path):
    try:
        tqdm.write(f"Converting {input_path} to {output_path}...", end="")
        ffmpeg.input(input_path).output(output_path, audio_bitrate='320k', loglevel="panic").run(overwrite_output=True)

    except ffmpeg.Error as e:
        print(f"Failed to convert {file_path}: {e}")


def convert_files(inout_pairs):
    for i, o in inout_pairs:
        convert_to_mp3(i, o)


def copy_directory_structure(input_dir, output_dir):
    for root, dirs, files in os.walk(input_dir):
        relative_path = os.path.relpath(root, input_dir)
        output_path = os.path.join(output_dir, relative_path)
        os.makedirs(output_path, exist_ok=True)


def get_total_files(dir):
    res = []
    for root, dirs, files in os.walk(dir):

        for file in files:
            file_path = os.path.join(root, file)
            file_name, file_extension = os.path.splitext(file)
            if file_extension.lower() in SUPPORTED_EXTENSIONS:
                res.append(file_path)

    return res


def main(in_dir, out_dir):

    print("Copying directory structure...")
    copy_directory_structure(in_dir, out_dir)

    NUM_THREADS = 8
    print(f"Converting files... Number of threads: {NUM_THREADS}")
    files = get_total_files(in_dir)
    total_files = len(files)
    out_files = [os.path.join(out_dir, os.path.relpath(f, in_dir)) for f in files]
    # print(files[1])
    # print(out_files[1])
    # s= input ("continue?")
    # if s != "y":
    #     return

    with tqdm(total=total_files) as pbar:
        with ThreadPoolExecutor(max_workers=NUM_THREADS) as pool:
            stopping = threading.Event()
            def runner(fun, *args, **kwargs):
                try:
                    if not stopping.is_set():
                        fun(*args, **kwargs)
                except :
                    stopping.set()

            fut = {}
            for i in range(total_files):
                if stopping.is_set():
                    continue

                fut[pool.submit(runner, convert_to_mp3, files[i], out_files[i])] = i

            try:
                for f in concurrent.futures.as_completed(fut):
                    i = fut[f]
                    if stopping.is_set():
                        break
                        fut[i] = f.result()
                    pbar.update(1)
            except KeyboardInterrupt:
                pass


if __name__ == "__main__":
    main(*sys.argv[1:])
