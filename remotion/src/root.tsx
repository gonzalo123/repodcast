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
    defaultProps={{episode: {title: 'Repodcast', slides: [], source_commit: null}, audioFiles: []}}
    calculateMetadata={({props}) => ({
      durationInFrames: Math.max(1, props.episode.slides.reduce((sum, slide) => sum + slide.duration_seconds * 30, 0)),
    })}
  />
);
