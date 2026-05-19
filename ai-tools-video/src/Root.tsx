import './index.css';
import { Composition } from 'remotion';
import { MainComposition } from './Composition';

const FPS = 30;
// Total duration based on audio: 11064 frames - 90 transition frames = 10974 frames
const DURATION_IN_FRAMES = 10974;

export const RemotionRoot: React.FC = () => {
  return (
    <>
      <Composition
        id="AIToolsVideo"
        component={MainComposition}
        durationInFrames={DURATION_IN_FRAMES}
        fps={FPS}
        width={1920}
        height={1080}
      />
    </>
  );
};
