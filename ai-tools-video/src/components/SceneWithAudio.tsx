import React from 'react';
import { Audio } from '@remotion/media';
import { staticFile } from 'remotion';

interface SceneWithAudioProps {
  audioFile: string;
  children: React.ReactNode;
}

export const SceneWithAudio: React.FC<SceneWithAudioProps> = ({
  audioFile,
  children,
}) => {
  return (
    <>
      {children}
      <Audio src={staticFile(`voiceover/${audioFile}`)} />
    </>
  );
};
