# 视频片头合并工具

这是一个用于合并视频片头与主视频的工具，支持多种视频编码格式。该工具使用 `ffmpeg` 进行视频处理，能够自动提取视频和音频参数，确保合并后的视频质量。

## 功能

- 重新编码片头视频以匹配主视频的参数
- 使用 `concat` demuxer 合并视频
- 支持 H.264 和 HEVC (H.265) 编码
- 自动处理时间戳和同步问题

## 依赖

- Python 3.x
- `ffmpeg` 和 `ffprobe`（请确保已安装并在系统路径中）

## 安装

1. 克隆此仓库：
   ```bash
   git clone https://github.com/yourusername/video-merge-tool.git
   cd video-merge-tool
   ```

2. 安装依赖（如果有）：
   ```bash
   pip install -r requirements.txt
   ```

## 使用方法

运行以下命令以合并视频片头和主视频：

```bash
python main.py <片头视频文件路径> <主视频文件路径> <输出视频文件路径>
```

### 示例

```bash
python main.py intro.mp4 main.mp4 output.mp4
```

## 函数说明

### `get_video_params(video_path)`

提取视频的编码参数，包括编码格式、宽度、高度和帧率。

### `get_audio_params(video_path)`

提取音频的编码参数，包括编码格式、声道数和采样率。

### `reencode_intro(intro_path, main_path, output_path)`

重新编码片头以完全匹配主视频参数。

### `convert_to_ts(input_path, output_path)`

将视频转换为 TS 格式。

### `create_concat_file(intro_path, main_path, concat_file)`

创建用于合并视频的 concat 文件。

### `get_cache_dir()`

获取缓存目录路径。

### `get_temp_dir()`

创建带有唯一标识的临时目录。

### `merge_videos(intro_path, main_path, output_path)`

使用 concat demuxer 合并视频，处理时间戳。

### `cleanup_temp_files(*files)`

清理临时文件。

## 注意事项

- 请确保 `ffmpeg` 和 `ffprobe` 已正确安装并可在命令行中访问。
- 该工具会在当前目录下创建一个名为 `videos_cache` 的缓存目录，用于存储临时文件。

## 许可证

此项目采用 MIT 许可证，详细信息请查看 [LICENSE](LICENSE) 文件。
