import { useEffect, useMemo, useState } from "react";

export function useTypewriter(text: string, speed = 18) {
  const [index, setIndex] = useState(0);

  useEffect(() => {
    setIndex(0);
  }, [text]);

  useEffect(() => {
    if (!text) {
      return;
    }
    if (index >= text.length) {
      return;
    }

    const timer = setTimeout(() => {
      setIndex((prev) => prev + 1);
    }, speed);

    return () => clearTimeout(timer);
  }, [index, speed, text]);

  return useMemo(() => text.slice(0, index), [index, text]);
}
