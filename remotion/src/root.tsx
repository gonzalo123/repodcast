import {Composition} from 'remotion';
import {RepodcastVideo, type VideoProps} from './video';

export const Root = () => (
  <Composition
    id="Repodcast"
    component={RepodcastVideo}
    width={1920}
    height={1080}
    fps={30}
    durationInFrames={30}
    defaultProps={{episode: {title: 'Repodcast', slides: [], source_commit: 'a73f21c8b942', source_url: null, source_repository: 'gonzalo123/repodcast', source_paths: ['src/application/build_video.py', 'src/audio/renderer.py', 'src/domain/episode.py', 'src/video/remotion.py', 'remotion/src/video.tsx'], intro_duration_seconds: 4, outro_duration_seconds: 4}, audioFiles: []}}
    calculateMetadata={({props}) => ({
      durationInFrames: Math.max(1, (((props.episode.intro_duration_seconds ?? 4) + (props.episode.outro_duration_seconds ?? 4)) * 30) + props.episode.slides.reduce((sum, slide) => sum + slide.duration_seconds * 30, 0)),
    })}
  />
);
