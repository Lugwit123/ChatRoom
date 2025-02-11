// src/components/PlyrPlayer.tsx
import React from 'react';
import Plyr from 'plyr-react';
import 'plyr-react/plyr.css';
import './PlyrPlayer.css'; // 自定义样式文件（可选）

interface PlyrPlayerProps {
  videoUrl: string;
}

const PlyrPlayer: React.FC<PlyrPlayerProps> = ({ videoUrl }) => {
  const plyrOptions: Plyr.Options = {
    controls: [
      'play-large',     // 大播放按钮
      'play',           // 播放/暂停按钮
      'rewind',         // 倒退按钮
      'fast-forward',   // 快进按钮
      'progress',       // 播放进度条
      'current-time',   // 当前时间
      'mute',           // 静音按钮
      'volume',         // 音量控制
      'fullscreen'      // 全屏按钮
    ],
    autoplay: true,     // 自动播放
    loop: { active: false }, // 是否循环播放
    muted: false,        // 是否默认静音
    volume: 0.5,         // 默认音量
  };

  // 生成视频标题（从 URL 提取文件名）
  const getVideoTitle = (url: string) => {
    try {
      const urlObj = new URL(url);
      const pathname = urlObj.pathname;
      const filename = pathname.substring(pathname.lastIndexOf('/') + 1);
      return filename ? filename : `视频`;
    } catch (error) {
      return `视频`;
    }
  };

  return (
    <div className="plyr-player-container">
      <div className="plyr-player">
        <Plyr
          key={videoUrl} // 通过 key 强制重新渲染组件以加载新视频
          source={{
            type: 'video',
            sources: [
              {
                src: videoUrl,
                type: 'video/mp4',
              },
            ],
          }}
          options={plyrOptions}
        />
      </div>
      <div className="video-title">
        <h3>{getVideoTitle(videoUrl)}</h3>
      </div>
    </div>
  );
};

export default PlyrPlayer;
