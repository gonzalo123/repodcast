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
    defaultProps={{episode: {title: 'Repodcast', slides: [], source_commit: null, source_url: null, source_repository: 'gonzalo123/repodcast', intro_duration_seconds: 4}, audioFiles: []}}
    calculateMetadata={({props}) => ({
      durationInFrames: Math.max(1, ((props.episode.intro_duration_seconds ?? 4) * 30) + props.episode.slides.reduce((sum, slide) => sum + slide.duration_seconds * 30, 0)),
    })}
  />
);
