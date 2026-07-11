import {Audio} from '@remotion/media';
import {Highlight, themes, type Language} from 'prism-react-renderer';
import {
  AbsoluteFill,
  Easing,
  interpolate,
  Series,
  spring,
  staticFile,
  useCurrentFrame,
  useVideoConfig,
} from 'remotion';
import './style.css';

type Slide = {
  index: number;
  title: string;
  bullets: string[];
  narration: string;
  duration_seconds: number;
  visual_hint?: string | null;
  code_snippet?: string | null;
  code_language?: string | null;
  code_path?: string | null;
  visual?: ArchitectureFlow | null;
};
type FlowNode = {id: string; label: string; path?: string | null};
type FlowEdge = {from_id: string; to_id: string};
type ArchitectureFlow = {type: 'flow'; nodes: FlowNode[]; edges: FlowEdge[]};
type Episode = {
  title: string;
  slides: Slide[];
  source_commit?: string | null;
  source_url?: string | null;
  source_repository?: string | null;
  source_paths?: string[];
  intro_duration_seconds?: number;
  outro_duration_seconds?: number;
};
export type VideoProps = {episode: Episode; audioFiles: string[]};

const supportedLanguages = new Set(['markup', 'bash', 'css', 'javascript', 'typescript', 'jsx', 'tsx', 'python', 'json', 'yaml', 'toml', 'java', 'go', 'rust', 'php', 'ruby', 'sql']);

const repositoryLabel = (sourceUrl?: string | null) => {
  if (!sourceUrl) return null;
  return sourceUrl
    .replace(/^https?:\/\/(?:www\.)?github\.com\//, '')
    .replace(/\.git$/, '')
    .replace(/\/$/, '');
};

const Intro = ({episode}: {episode: Episode}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const durationInFrames = (episode.intro_duration_seconds ?? 4) * fps;
  const titleEntrance = spring({frame: frame - 16, fps, config: {damping: 18, mass: 0.8}});
  const metaEntrance = spring({frame: frame - 28, fps, config: {damping: 20}});
  const exit = interpolate(frame, [durationInFrames - 15, durationInFrames], [1, 0], {extrapolateLeft: 'clamp'});
  const repository = repositoryLabel(episode.source_url) ?? episode.source_repository;
  const paths = (episode.source_paths ?? []).slice(0, 7);
  const scan = interpolate(frame, [0, Math.max(1, durationInFrames - 18)], [-8, 108], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'});

  return <AbsoluteFill className="intro" style={{opacity: exit}}>
    <div className="technicalGrid" />
    <div className="scanLine" style={{left: `${scan}%`}} />
    <div className="repositoryTree" aria-hidden="true">
      {paths.map((path, index) => {
        const reveal = spring({frame: frame - index * 5, fps, config: {damping: 22}});
        return <div key={path} style={{opacity: reveal * .16, transform: `translateX(${(1 - reveal) * 28}px)`}}>
          <span>{String(index + 1).padStart(2, '0')}</span>{path}
        </div>;
      })}
    </div>
    <div className="introStage">
      <div className="introHeader"><span>REPODCAST</span><span>REPOSITORY ANALYSIS</span></div>
      <div className="introCopy" style={{opacity: titleEntrance, transform: `translateY(${(1 - titleEntrance) * 45}px)`}}>
        <div className="introEyebrow">TECHNICAL WALKTHROUGH</div>
        <h1>{episode.title}</h1>
        <p>A repository, explained.</p>
      </div>
      <div className="introMeta" style={{opacity: metaEntrance}}>
        <span>{repository ?? 'LOCAL REPOSITORY'}</span>
        {episode.source_commit && <span>COMMIT {episode.source_commit.slice(0, 12)}</span>}
      </div>
    </div>
  </AbsoluteFill>;
};

const Outro = ({episode}: {episode: Episode}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const durationInFrames = (episode.outro_duration_seconds ?? 4) * fps;
  const entrance = spring({frame: frame - 8, fps, config: {damping: 20, mass: .9}});
  const signature = spring({frame: frame - 28, fps, config: {damping: 22}});
  const exit = interpolate(frame, [durationInFrames - 12, durationInFrames], [1, 0], {extrapolateLeft: 'clamp'});
  const repository = repositoryLabel(episode.source_url) ?? episode.source_repository;

  return <AbsoluteFill className="outro" style={{opacity: exit}}>
    <div className="technicalGrid" />
    <div className="outroStage">
      <div className="outroHeader">REPODCAST</div>
      <div className="outroCopy" style={{opacity: entrance, transform: `translateY(${(1 - entrance) * 35}px)`}}>
        <div className="outroEyebrow">END OF WALKTHROUGH</div>
        <h1>{episode.title}</h1>
        {repository && <p>{repository}{episode.source_commit ? ` · ${episode.source_commit.slice(0, 12)}` : ''}</p>}
      </div>
      <div className="outroSignature" style={{opacity: signature}}><span>CREATED BY</span><strong>gonzalo123</strong></div>
    </div>
  </AbsoluteFill>;
};

const CodeBlock = ({code, language, path}: {code: string; language?: string | null; path?: string | null}) => {
  const frame = useCurrentFrame();
  const {durationInFrames} = useVideoConfig();
  const selected = supportedLanguages.has(language ?? '') ? language! as Language : 'plain' as Language;
  return <Highlight theme={themes.nightOwl} code={code.trim()} language={selected}>
    {({tokens, getLineProps, getTokenProps}) => <pre className="codeWindow">
      <div className="window">
        <div className="traffic"><i/><i/><i/></div>
        <span className="codePath">{path || 'source code'}</span>
        <span className="codeLanguage">{language || 'text'}</span>
      </div>
      <code className="highlightedCode">
        {tokens.map((line, lineIndex) => {
          const reveal = interpolate(frame, [8 + lineIndex * 4, 16 + lineIndex * 4], [0, 1], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'});
          const activeLine = Math.floor(interpolate(frame, [28, Math.max(29, durationInFrames - 22)], [0, Math.max(0, tokens.length - .001)], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'}));
          const isActive = lineIndex === activeLine && frame >= 24;
          const focusOpacity = frame < 24 || isActive ? 1 : lineIndex < activeLine ? .68 : .42;
          return <div {...getLineProps({line})} className={`codeLine${isActive ? ' isActive' : ''}`} key={lineIndex} style={{opacity: reveal * focusOpacity, transform: `translateX(${(1 - reveal) * 16}px)`}}>
            <span className="lineNumber">{String(lineIndex + 1).padStart(2, '0')}</span>
            <span>{line.map((token, tokenIndex) => <span {...getTokenProps({token})} key={tokenIndex} />)}</span>
          </div>;
        })}
      </code>
    </pre>}
  </Highlight>;
};

const nodePosition = (index: number, count: number) => {
  if (count <= 4) return {x: 100 + index * (800 / Math.max(1, count - 1)), y: 215};
  const topCount = Math.ceil(count / 2);
  const row = index < topCount ? 0 : 1;
  const position = row === 0 ? index : index - topCount;
  const rowCount = row === 0 ? topCount : count - topCount;
  return {x: 100 + position * (800 / Math.max(1, rowCount - 1)), y: row === 0 ? 105 : 325};
};

// mitad de caja (190x118px) proyectada sobre el viewBox 1000x430 del .flowWrap
const NODE_HALF_W = 82;
const NODE_HALF_H = 41;

// ponytail: mueve (px,py) al borde del rectángulo hw/hh centrado en (qx,qy), en dirección hacia (px,py)
const clipToBox = (px: number, py: number, qx: number, qy: number, hw: number, hh: number) => {
  const dx = px - qx, dy = py - qy;
  const s = 1 / Math.max(Math.abs(dx) / hw, Math.abs(dy) / hh, 1e-6);
  return {x: qx + dx * s, y: qy + dy * s};
};

const FlowDiagram = ({flow, commit}: {flow: ArchitectureFlow; commit?: string | null}) => {
  const frame = useCurrentFrame();
  const {fps, durationInFrames} = useVideoConfig();
  const positions = new Map(flow.nodes.map((node, index) => [node.id, nodePosition(index, flow.nodes.length)]));
  const segmentFrames = Math.max(18, (durationInFrames - 36) / Math.max(1, flow.nodes.length));
  const activeNode = Math.floor(interpolate(frame, [18, Math.max(19, durationInFrames - 18)], [0, Math.max(0, flow.nodes.length - .001)], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'}));
  return <div className="flowWrap">
    <svg className="flowEdges" viewBox="0 0 1000 430" preserveAspectRatio="none">
      <defs><marker id="arrow" markerWidth="8" markerHeight="8" refX="7" refY="4" orient="auto"><path d="M0,0 L8,4 L0,8 Z" /></marker></defs>
      {flow.edges.map((edge, index) => {
        const from = positions.get(edge.from_id); const to = positions.get(edge.to_id);
        if (!from || !to) return null;
        const start = clipToBox(to.x, to.y, from.x, from.y, NODE_HALF_W, NODE_HALF_H);
        const end = clipToBox(from.x, from.y, to.x, to.y, NODE_HALF_W, NODE_HALF_H);
        const len = Math.hypot(end.x - start.x, end.y - start.y);
        const reveal = interpolate(frame, [12 + index * 8, 24 + index * 8], [0, 1], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'});
        const signalStart = 18 + (index + 1) * segmentFrames - 12;
        const signal = interpolate(frame, [signalStart, signalStart + 18], [0, 1], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'});
        const isSignalVisible = signal > 0 && signal < 1;
        return <g key={`${edge.from_id}-${edge.to_id}`}>
          <line className={index < activeNode ? 'isPassed' : index === activeNode ? 'isActive' : ''} x1={start.x} y1={start.y} x2={end.x} y2={end.y} markerEnd="url(#arrow)" strokeDasharray={len} style={{opacity: reveal, strokeDashoffset: (1 - reveal) * len}} />
          <circle className="flowSignal" cx={start.x + (end.x - start.x) * signal} cy={start.y + (end.y - start.y) * signal} r="7" style={{opacity: isSignalVisible ? 1 : 0}} />
        </g>;
      })}
    </svg>
    {flow.nodes.map((node, index) => {
      const point = positions.get(node.id)!;
      const reveal = spring({frame: frame - index * 7, fps, config: {damping: 16}});
      const state = index === activeNode ? ' isActive' : index < activeNode ? ' isPassed' : ' isUpcoming';
      const stateOpacity = index === activeNode ? 1 : index < activeNode ? .72 : .42;
      const scale = .82 + reveal * .18 + (index === activeNode ? .035 : 0);
      return <div className={`flowNode${state}`} key={node.id} style={{left: `${point.x / 10}%`, top: `${point.y / 4.3}%`, opacity: reveal * stateOpacity, transform: `translate(-50%, -50%) scale(${scale})`}}>
        <div className="flowIndex">{String(index + 1).padStart(2, '0')}</div>
        <strong>{node.label}</strong>
        {node.path && <small>{node.path}</small>}
      </div>;
    })}
    {commit && <div className="commit">ANALYZED FROM COMMIT <b>{commit.slice(0, 12)}</b></div>}
  </div>;
};

const Scene = ({slide, total, audio, commit, repository}: {slide: Slide; total: number; audio: string; commit?: string | null; repository?: string | null}) => {
  const frame = useCurrentFrame();
  const {fps, durationInFrames} = useVideoConfig();
  const entrance = spring({frame, fps, config: {damping: 18, mass: 0.8}});
  const exit = interpolate(frame, [durationInFrames - 15, durationInFrames], [1, 0], {extrapolateLeft: 'clamp'});
  const drift = interpolate(frame, [0, durationInFrames], [0, 32], {easing: Easing.inOut(Easing.ease)});
  const isCover = slide.index === 1;
  const isCode = Boolean(slide.code_snippet);
  const isFlow = Boolean(slide.visual?.type === 'flow');

  return (
    <AbsoluteFill className="scene" style={{opacity: exit}}>
      <Audio src={staticFile(audio)} />
      <div className="orb orbOne" style={{transform: `translate(${drift}px, ${drift / 2}px)`}} />
      <div className="orb orbTwo" style={{transform: `translate(${-drift}px, ${drift}px)`}} />
      <header><span className="brand">REPODCAST</span><span className="sourceIdentity">{repository}{commit ? ` · ${commit.slice(0, 12)}` : ''}</span><span>{String(slide.index).padStart(2, '0')} / {String(total).padStart(2, '0')}</span></header>
      <main className={isCover ? 'cover' : isCode ? 'codeLayout' : isFlow ? 'flowLayout' : 'content'} style={{transform: `translateY(${(1 - entrance) * 50}px)`, opacity: entrance}}>
        <div className="copy">
          {!isCover && <div className="eyebrow">TECHNICAL WALKTHROUGH</div>}
          <h1>{slide.title}</h1>
          {isCover && <p className="lead">A repository, explained.</p>}
          {!isCover && !isCode && !isFlow && <div className="bullets">
            {slide.bullets.map((bullet, i) => {
              const reveal = spring({frame: frame - 8 - i * 7, fps, config: {damping: 20}});
              return <div className="bullet" key={bullet} style={{opacity: reveal, transform: `translateX(${(1 - reveal) * 35}px)`}}><span>{i + 1}</span>{bullet}</div>;
            })}
          </div>}
          {slide.visual_hint && !isCover && !isCode && !isFlow && <div className="hint">{slide.visual_hint}</div>}
        </div>
        {isCode && slide.code_snippet && <CodeBlock code={slide.code_snippet} language={slide.code_language} path={slide.code_path} />}
        {isFlow && slide.visual && <FlowDiagram flow={slide.visual} commit={commit} />}
      </main>
      <footer><div className="progress" style={{width: `${(slide.index / total) * 100}%`}} /></footer>
    </AbsoluteFill>
  );
};

export const RepodcastVideo = ({episode, audioFiles}: VideoProps) => {
  const introDurationInFrames = (episode.intro_duration_seconds ?? 4) * 30;
  const outroDurationInFrames = (episode.outro_duration_seconds ?? 4) * 30;
  const repository = repositoryLabel(episode.source_url) ?? episode.source_repository;
  return <AbsoluteFill className="video">
    <Series>
      {introDurationInFrames > 0 && <Series.Sequence durationInFrames={introDurationInFrames}>
        <Intro episode={episode} />
      </Series.Sequence>}
      {episode.slides.map((slide, index) => (
        <Series.Sequence key={slide.index} durationInFrames={slide.duration_seconds * 30}>
          <Scene slide={slide} total={episode.slides.length} audio={audioFiles[index]} commit={episode.source_commit} repository={repository} />
        </Series.Sequence>
      ))}
      {outroDurationInFrames > 0 && <Series.Sequence durationInFrames={outroDurationInFrames}>
        <Outro episode={episode} />
      </Series.Sequence>}
    </Series>
  </AbsoluteFill>;
};
