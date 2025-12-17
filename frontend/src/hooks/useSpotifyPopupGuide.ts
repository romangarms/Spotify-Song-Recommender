import { useRef, useCallback, useEffect } from 'react';

interface UseSpotifyPopupGuideOptions {
  /** URL to open in the Spotify popup */
  spotifyUrl: string;
  /** Function to validate if clipboard content is valid input */
  isValidInput: (text: string) => boolean;
  /** Callback when valid input is detected from clipboard */
  onInputDetected: (text: string) => void;
}

interface UseSpotifyPopupGuideReturn {
  /** Opens the Spotify popup on the right half of the screen */
  openPopup: () => void;
  /** Manually check clipboard for valid input */
  checkClipboard: () => Promise<void>;
  /** Close the popup if it's open */
  closePopup: () => void;
  /** Reference to the popup window */
  popupRef: React.MutableRefObject<Window | null>;
}

/**
 * Hook for managing a split-screen Spotify popup guide.
 * Handles popup positioning, clipboard detection, and visibility changes.
 */
export function useSpotifyPopupGuide({
  spotifyUrl,
  isValidInput,
  onInputDetected,
}: UseSpotifyPopupGuideOptions): UseSpotifyPopupGuideReturn {
  const popupRef = useRef<Window | null>(null);

  const openPopup = useCallback(() => {
    const width = Math.floor(window.screen.availWidth / 2);
    const height = window.screen.availHeight;
    const left = Math.floor(window.screen.availWidth / 2);
    popupRef.current = window.open(
      spotifyUrl,
      'spotify',
      `width=${width},height=${height},left=${left},top=0`
    );
  }, [spotifyUrl]);

  const checkClipboard = useCallback(async () => {
    try {
      const text = await navigator.clipboard.readText();
      if (isValidInput(text)) {
        onInputDetected(text);
      }
    } catch {
      // Clipboard access denied or not available - silently ignore
    }
  }, [isValidInput, onInputDetected]);

  // Auto-check clipboard when page becomes visible (user switches back from Spotify)
  useEffect(() => {
    const handleVisibilityChange = () => {
      if (document.visibilityState === 'visible') {
        checkClipboard();
      }
    };

    document.addEventListener('visibilitychange', handleVisibilityChange);
    return () => document.removeEventListener('visibilitychange', handleVisibilityChange);
  }, [checkClipboard]);

  const closePopup = useCallback(() => {
    if (popupRef.current && !popupRef.current.closed) {
      popupRef.current.close();
    }
  }, []);

  return { openPopup, checkClipboard, closePopup, popupRef };
}
