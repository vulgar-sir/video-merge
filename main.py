import subprocess
import json
import os
import argparse
import sys
import uuid
import time


def get_video_params(video_path):
    """提取视频的编码参数"""
    cmd = [
        "ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries",
        "stream=codec_name,width,height,r_frame_rate", "-of", "json", video_path
    ]
    result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    video_info = json.loads(result.stdout)
    return video_info['streams'][0]


def get_audio_params(video_path):
    """提取音频的编码参数"""
    cmd = [
        "ffprobe", "-v", "error", "-select_streams", "a:0", "-show_entries",
        "stream=codec_name,channels,sample_rate", "-of", "json", video_path
    ]
    result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    audio_info = json.loads(result.stdout)
    return audio_info['streams'][0]


def reencode_intro(intro_path, main_path, output_path):
    """重新编码片头以完全匹配主视频参数"""
    video_params = get_video_params(main_path)
    audio_params = get_audio_params(main_path)

    video_codec = video_params['codec_name']
    width = video_params['width']
    height = video_params['height']
    frame_rate = video_params['r_frame_rate']

    audio_codec = audio_params['codec_name']
    channels = audio_params['channels']
    sample_rate = audio_params['sample_rate']

    # 根据视频编码选择正确的编码器
    if video_codec == 'h264':
        encoder = 'libx264'
        profile = 'high'
    elif video_codec == 'hevc':
        encoder = 'libx265'
        profile = 'main'
    else:
        raise ValueError(f"Unsupported video codec: {video_codec}")

    # 调用 ffmpeg 重新编码片头，完全匹配主视频参数
    cmd = [
        "ffmpeg", "-y", "-i", intro_path,
        # 视频参数
        "-c:v", encoder,
        "-vf", f"scale={width}:{height},fps={frame_rate}",
        "-profile:v", profile,
        "-pix_fmt", "yuv420p",
        # 音频参数
        "-c:a", audio_codec,
        "-ac", str(channels),
        "-ar", str(sample_rate),
        # 时间戳和同步处理
        "-fps_mode", "cfr",
        "-async", "1",
        # 强制关键帧间隔
        "-g", "24",
        "-keyint_min", "24",
        # 时间戳处理
        "-fflags", "+genpts",
        "-movflags", "+faststart",
        "-avoid_negative_ts", "make_zero",
        output_path
    ]
    subprocess.run(cmd)


def convert_to_ts(input_path, output_path):
    """将视频转换为ts格式"""
    cmd = [
        "ffmpeg", "-y", "-i", input_path,
        "-c", "copy", "-bsf:v", "h264_mp4toannexb", "-f", "mpegts",
        output_path
    ]
    subprocess.run(cmd)


def create_concat_file(intro_path, main_path, concat_file):
    """创建concat文件"""
    with open(concat_file, 'w', encoding='utf-8') as f:
        f.write(f"file '{os.path.abspath(intro_path)}'\n")
        f.write(f"file '{os.path.abspath(main_path)}'\n")


def get_cache_dir():
    """获取缓存目录路径"""
    # 获取当前执行文件所在目录
    exe_dir = os.path.dirname(os.path.abspath(sys.argv[0]))
    cache_dir = os.path.join(exe_dir, "videos_cache")
    
    # 确保缓存目录存在
    if not os.path.exists(cache_dir):
        os.makedirs(cache_dir)
    
    return cache_dir


def get_temp_dir():
    """创建带有唯一标识的临时目录"""
    unique_id = str(uuid.uuid4())[:8]
    timestamp = int(time.time())
    cache_dir = get_cache_dir()
    temp_dir = os.path.join(cache_dir, f"temp_segments_{timestamp}_{unique_id}")
    return temp_dir


def merge_videos(intro_path, main_path, output_path):
    """使用concat demuxer合并视频，处理时间戳"""
    # 创建带有唯一标识的临时目录
    temp_dir = get_temp_dir()
    concat_list = os.path.join(temp_dir, "concat.txt")
    if not os.path.exists(temp_dir):
        os.makedirs(temp_dir)
    
    try:
        # 使用唯一标识命名临时文件
        intro_ts = os.path.join(temp_dir, f"intro_{os.path.basename(intro_path)}.ts")
        main_ts = os.path.join(temp_dir, f"main_{os.path.basename(main_path)}.ts")
        
        # 获取主视频的编码信息
        video_params = get_video_params(main_path)
        video_codec = video_params['codec_name']
        
        # 选择正确的 bitstream filter
        if video_codec == 'h264':
            bsf = 'h264_mp4toannexb'
        elif video_codec == 'hevc':
            bsf = 'hevc_mp4toannexb'
        else:
            raise ValueError(f"Unsupported video codec: {video_codec}")
        
        # 转换片头
        cmd1 = [
            "ffmpeg", "-y",
            "-i", intro_path,
            "-c:v", "copy",
            "-c:a", "aac",
            "-bsf:v", bsf,
            "-f", "mpegts",
            "-muxdelay", "0",
            "-muxpreload", "0",
            intro_ts
        ]
        subprocess.run(cmd1)
        
        # 转换主视频
        cmd2 = [
            "ffmpeg", "-y",
            "-i", main_path,
            "-c:v", "copy",
            "-c:a", "aac",
            "-bsf:v", bsf,
            "-f", "mpegts",
            "-muxdelay", "0",
            "-muxpreload", "0",
            main_ts
        ]
        subprocess.run(cmd2)
        
        # 创建concat列表文件
        intro_ts_abs = os.path.abspath(intro_ts)
        main_ts_abs = os.path.abspath(main_ts)
        with open(concat_list, 'w', encoding='utf-8') as f:
            f.write(f"file '{intro_ts_abs}'\n")
            f.write(f"file '{main_ts_abs}'\n")
        
        # 合并ts文件
        cmd3 = [
            "ffmpeg", "-y",
            "-f", "concat",
            "-safe", "0",
            "-i", concat_list,
            "-c", "copy",
            "-movflags", "+faststart",
            "-fflags", "+igndts",
            "-async", "1",
            output_path
        ]
        result = subprocess.run(cmd3, capture_output=True, text=True)
        if result.returncode != 0:
            raise RuntimeError(f"合并失败: {result.stderr}")
        
        return True  # 返回成功标志
        
    except Exception as e:
        print(f"处理过程中出错: {str(e)}")
        return False  # 返回失败标志
        
    finally:
        # 清理临时文件和目录
        for file in [intro_ts, main_ts, concat_list]:
            if os.path.exists(file):
                os.remove(file)
        if os.path.exists(temp_dir):
            os.rmdir(temp_dir)


def cleanup_temp_files(*files):
    """清理临时文件"""
    for file in files:
        try:
            if os.path.exists(file):
                os.remove(file)
        except Exception as e:
            print(f"清理临时文件时出错: {e}")


if __name__ == "__main__":
    # 设置命令行参数
    parser = argparse.ArgumentParser(description='视频片头合并工具')
    parser.add_argument('intro_path', help='片头视频文件路径')
    parser.add_argument('main_path', help='主视频文件路径')
    parser.add_argument('output_path', help='输出视频文件路径')
    
    args = parser.parse_args()

    # 获取带有唯一标识的临时文件名
    unique_id = str(uuid.uuid4())[:8]
    timestamp = int(time.time())
    cache_dir = get_cache_dir()
    encoded_intro = os.path.join(cache_dir, f"intro_{timestamp}_{unique_id}_encoded.mp4")

    try:
        # 重新编码片头以匹配主视频参数
        reencode_intro(args.intro_path, args.main_path, encoded_intro)
        print(f"片头已重新编码为 {encoded_intro}")

        # 合并视频
        if merge_videos(encoded_intro, args.main_path, args.output_path):
            print(f"视频已合并为 {args.output_path}")  # 只在成功时显示
        else:
            print("视频合并失败")

    finally:
        # 清理临时文件
        cleanup_temp_files(encoded_intro)
        # 尝试清理缓存目录（如果为空）
        try:
            if os.path.exists(cache_dir) and not os.listdir(cache_dir):
                os.rmdir(cache_dir)
        except Exception as e:
            print(f"清理缓存目录时出错: {e}")
