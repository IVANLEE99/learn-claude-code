import { staticFile } from 'remotion';

export const getAudioDuration = async (file: string): Promise<number> => {
  const url = staticFile(file);
  const response = await fetch(url);
  const blob = await response.blob();

  return new Promise((resolve) => {
    const audio = new Audio();
    audio.src = URL.createObjectURL(blob);
    audio.addEventListener('loadedmetadata', () => {
      resolve(audio.duration);
    });
    audio.addEventListener('error', () => {
      resolve(30); // fallback to 30 seconds
    });
  });
};

export const SCENE_DURATIONS = {
  scene1: 816,   // 27.2s
  scene2: 1839,  // 61.3s
  scene3: 1704,  // 56.8s
  scene4: 1683,  // 56.1s
  scene5: 1533,  // 51.1s
  scene6: 1485,  // 49.5s
  scene7: 2004,  // 66.8s
};
