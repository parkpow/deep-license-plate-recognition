export interface PlateCandidate {
  value: string;
  score: number;
}

export interface ColorInfo {
  color: string;
  score: number;
}

export interface MakeModel {
  make: string;
  model: string;
  score: number;
}

export interface Orientation {
  orientation: string;
  score: number;
}

export interface Box {
  xmin: number;
  ymin: number;
  xmax: number;
  ymax: number;
}

export interface Region {
  code: string;
  score: number;
}

export interface Vehicle {
  box: Box;
  score: number;
  type: string;
}

export interface PlateProps {
  plate: PlateCandidate[];
  region: { value: string; score: number }[];
}

export interface VehicleProps {
  make_model: MakeModel[];
  orientation: { value: string; score: number }[];
  color: { value: string; score: number }[];
}

export interface VehicleType2 {
  type: string;
  score: number;
  box: Box;
  props: VehicleProps;
}

export interface PlateType2 {
  type: string;
  score: number;
  box: Box;
  props: PlateProps;
}

export interface ResultType1 {
  box: Box;
  candidates: PlateCandidate[];
  color: ColorInfo[];
  direction: number;
  speed: number;
  speed_score: number;
  dscore: number;
  model_make: MakeModel[];
  orientation: Orientation[];
  plate: string;
  position_sec: string;
  region: Region;
  score: number;
  source_url: string;
  user_data: string;
  vehicle: Vehicle;
}

export interface ResultType2 {
  plate: PlateType2;
  vehicle: VehicleType2;
  direction: number | null;
  speed: number | null;
  speed_score: number;
  source_url: string;
  position_sec: number;
  user_data: string;
}

export interface WebhookDataType1 {
  data: {
    camera_id: string;
    filename: string;
    results: ResultType1[];
    timestamp: string;
    timestamp_local: string;
    timestamp_camera: string;
  };
  hook: {
    event: string;
    filename: string;
    id: string;
    target: string;
  };
  receivedAt?: string;
  image: {
    url: string;
  };
}

export interface WebhookDataType2 {
  data: {
    camera_id: string;
    filename: string;
    results: ResultType2[];
    timestamp: string;
    timestamp_local: string;
    timestamp_camera: string | null;
  };
  hook: {
    event: string;
    filename: string;
    id: string;
    target: string;
  };
  receivedAt?: string;
  image: {
    url: string;
  };
}

export type WebhookData = WebhookDataType1 | WebhookDataType2;

export function isType1(data: WebhookData): data is WebhookDataType1 {
  return (
    "data" in data &&
    "results" in data.data &&
    data.data.results.length > 0 &&
    "plate" in data.data.results[0] &&
    typeof data.data.results[0].plate === "string"
  );
}

export function isType2(data: WebhookData): data is WebhookDataType2 {
  return (
    "data" in data &&
    "results" in data.data &&
    data.data.results.length > 0 &&
    "plate" in data.data.results[0] &&
    typeof data.data.results[0].plate === "object"
  );
}
