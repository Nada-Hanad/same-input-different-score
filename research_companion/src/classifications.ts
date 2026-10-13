import type {Pair} from './model';

// Presentation only. Original class codes and scientific measurements remain unchanged.
const descriptions: Record<string, {label: string; meaning: string}> = {
  null: {
    label: 'No scoring-relevant change',
    meaning: 'No scoring-relevant source or installed-dependency change was identified in the evaluated fixed-input replay configuration. This is a recorded implementation classification, not missing data.',
  },
  refactor: {
    label: 'Behavior-preserving refactor',
    meaning: 'The release ledger classifies the inspected code changes as a refactor expected to preserve assessment behavior. That expectation is separate from the observed replay result.',
  },
  defensive: {
    label: 'Input handling change',
    meaning: 'The release changes guards or handling of input values. This category can include related parser or dependency changes; it does not imply that outcomes stayed unchanged.',
  },
  scoring: {
    label: 'Scoring-relevant change',
    meaning: 'A source or dependency change was identified that could alter a test outcome, score modifier, or grade. Relevant implementation changes need not produce observed score changes.',
  },
};
export function classificationLabel(code: string | null | undefined) {
  return code == null ? 'Not recorded' : descriptions[code]?.label ?? 'Not available';
}
export function classificationMeaning(code: string | null | undefined) {
  return code == null ? 'Implementation classification not recorded.' : descriptions[code]?.meaning ?? 'No description is available for this implementation classification.';
}
const inputDetails: Record<string, string> = {
  '1.3.3->1.3.5': 'The cookie test adds guards for absent input values.',
  '1.4.8->1.4.9': 'The SRI test adds input guards and handles pages without a Content-Type header; the parser dependency also changes.',
};
export function implementationReason(pair: Pair) {
  let reason = pair.class === 'defensive' ? inputDetails[pair.pair] : undefined;
  if (!reason && pair.class === 'scoring') reason = pair.release.scoring_change_from_diff || 'The release ledger records a potentially outcome-changing implementation difference.';
  if (pair.class === 'null') reason = 'No scoring-relevant implementation change was identified for this pair.';
  if (pair.class === 'refactor') reason = 'This pair is recorded as a refactor expected to preserve assessment behavior.';
  return reason ?? 'Implementation classification not available.';
}
export function pairExplanation(pair: Pair) {
  const observation = pair.T === 0
    ? 'No test-outcome differences were observed on the fixed reference corpus.'
    : pair.T == null
      ? 'Test-outcome differences were not recorded.'
      : `${pair.T.toLocaleString('en-US')} websites had a changed test outcome on the fixed reference corpus.`;
  return `${implementationReason(pair)} ${observation}`;
}
