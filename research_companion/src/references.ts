import catalogue from '../../docs/figure-references.json';
import type {Evidence} from './model';
export function manuscriptLocation(entry: Pick<Evidence,'id'|'manuscript_location'>) {
  return entry.manuscript_location;
}
export function figureDescription(path: string) {
  const basename=path.split('/').at(-1);
  const figure=catalogue.figures.find(f=>f.generated_assets.some(asset=>asset.split('/').at(-1)===basename));
  return figure ? `Figure ${figure.number} · ${figure.label}` : 'Supplementary study plot';
}
