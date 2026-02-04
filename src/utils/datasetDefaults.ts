interface DatasetDefaults {
  dateColumn?: string;
  metricColumn?: string;
  categoryColumn?: string;
  segmentColumn?: string;
  stageColumn?: string;
  [key: string]: string | undefined;
}

const STORAGE_KEY_PREFIX = 'dataset_defaults_';

export function getDatasetDefaults(datasetName: string): DatasetDefaults {
  try {
    const key = `${STORAGE_KEY_PREFIX}${datasetName}`;
    const stored = localStorage.getItem(key);
    return stored ? JSON.parse(stored) : {};
  } catch (error) {
    console.error('Error loading dataset defaults:', error);
    return {};
  }
}

export function saveDatasetDefault(
  datasetName: string,
  key: string,
  value: string
): void {
  try {
    const storageKey = `${STORAGE_KEY_PREFIX}${datasetName}`;
    const current = getDatasetDefaults(datasetName);
    const updated = { ...current, [key]: value };
    localStorage.setItem(storageKey, JSON.stringify(updated));
  } catch (error) {
    console.error('Error saving dataset default:', error);
  }
}

export function inferDefaultKeyFromQuestion(question: string): string | null {
  const lower = question.toLowerCase();

  if (lower.includes('date') || lower.includes('time') || lower.includes('timestamp')) {
    return 'dateColumn';
  }
  if (lower.includes('metric') || lower.includes('measure') || lower.includes('value')) {
    return 'metricColumn';
  }
  if (lower.includes('category') || lower.includes('group')) {
    return 'categoryColumn';
  }
  if (lower.includes('segment') || lower.includes('cohort') || lower.includes('customer')) {
    return 'segmentColumn';
  }
  if (lower.includes('stage') || lower.includes('status') || lower.includes('funnel')) {
    return 'stageColumn';
  }

  return null;
}

export function clearDatasetDefaults(datasetName: string): void {
  try {
    const key = `${STORAGE_KEY_PREFIX}${datasetName}`;
    localStorage.removeItem(key);
  } catch (error) {
    console.error('Error clearing dataset defaults:', error);
  }
}
