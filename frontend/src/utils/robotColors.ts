/**
 * Paleta de cores vibrantes e contrastantes para identificação visual única de cada robô AMR.
 */
export const AMR_PALETTE: string[] = [
  "#06b6d4", // 01: Ciano Elétrico
  "#8b5cf6", // 02: Violeta / Roxo
  "#f59e0b", // 03: Âmbar Dourado
  "#10b981", // 04: Esmeralda Menta
  "#ec4899", // 05: Rosa Neon
  "#3b82f6", // 06: Azul Cobalto
  "#14b8a6", // 07: Verde Azulado / Teal
  "#f97316", // 08: Laranja Coral
  "#a855f7", // 09: Magenta Púrpura
  "#eab308", // 10: Amarelo Canário
  "#6366f1", // 11: Índigo Profundo
  "#22c55e", // 12: Verde Limão Vívido
  "#0ea5e9", // 13: Azul Celeste
  "#d946ef", // 14: Fúcsia Intenso
  "#84cc16", // 15: Lima Cítrico
  "#f43f5e", // 16: Vermelho Carmim
];

/**
 * Retorna a cor única e consistente atribuída a um robô específico (ex: "AMR-01" -> Ciano).
 */
export function getAmrColor(amrId: string): string {
  const match = amrId.match(/\d+/);
  if (match) {
    const num = parseInt(match[0], 10);
    const index = (num - 1) % AMR_PALETTE.length;
    return AMR_PALETTE[index >= 0 ? index : 0];
  }

  // Fallback baseado no hash do ID se não houver dígito
  let hash = 0;
  for (let i = 0; i < amrId.length; i++) {
    hash = amrId.charCodeAt(i) + ((hash << 5) - hash);
  }
  return AMR_PALETTE[Math.abs(hash) % AMR_PALETTE.length];
}

/**
 * Converte cor hexadecimal para rgba com o canal alfa especificado.
 */
export function hexToRgba(hex: string, alpha: number): string {
  const cleanHex = hex.replace("#", "");
  const r = parseInt(cleanHex.substring(0, 2), 16);
  const g = parseInt(cleanHex.substring(2, 4), 16);
  const b = parseInt(cleanHex.substring(4, 6), 16);
  return `rgba(${r}, ${g}, ${b}, ${alpha})`;
}
