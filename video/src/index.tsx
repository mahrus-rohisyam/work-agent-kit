import React from "react";
import { Composition, Still, registerRoot } from "remotion";
import { FeatureLandscape, FeatureSquare, FeatureVertical } from "./Feature";
import { SocialStill } from "./Still";
import { Cover, CoverSpec, coverSpec } from "./Cover";
import { Tour, TourSpec, tourFrames, tourSpec } from "./Tour";
import { ShowcaseLandscape, ShowcaseSpec, ShowcaseVertical, showcaseFrames, showcaseSpec } from "./Showcase";
import { FPS, spec, stillSpec, totalFrames, Spec, StillSpec } from "./spec";

// Studio defaults. Real renders pass --props=brands/<brand>/briefs/<campaign>/<asset>.json
const sample: Spec = spec.parse({
  hook: "Say the result here.",
  clip: { src: "footage/example/demo.mp4", startSec: 0, endSec: 8, focus: [] },
  captions: [{ from: 0.3, to: 3, text: "Name the *action*" }],
  cta: "One next step.",
});
const sampleStill: StillSpec = stillSpec.parse({
  headline: "Say one specific thing.",
});

const meta = ({ props }: { props: Spec }) => {
  const p = spec.parse(props);
  return { durationInFrames: totalFrames(p), props: p };
};

const sampleShowcase: ShowcaseSpec = showcaseSpec.parse({
  scenes: [{ title: "One selling point.", caption: "What the *clip* shows", clip: { src: "footage/example/demo.mp4", startSec: 0, endSec: 8 } }],
  cta: "One next step.",
});
const showcaseMeta = ({ props }: { props: ShowcaseSpec }) => {
  const p = showcaseSpec.parse(props);
  return { durationInFrames: showcaseFrames(p), props: p };
};

const sampleTour: TourSpec = tourSpec.parse({ scenes: [{ kind: "opener", sec: 4, title: "Say what it does." }], cta: "One next step." });
const tourMeta = ({ props }: { props: TourSpec }) => {
  const p = tourSpec.parse(props);
  return { durationInFrames: tourFrames(p), props: p };
};

const Root: React.FC = () => (
  <>
    <Composition id="tour" component={Tour} schema={tourSpec} defaultProps={sampleTour}
      width={1920} height={1080} fps={FPS} durationInFrames={300} calculateMetadata={tourMeta} />
    <Composition id="showcase-vertical" component={ShowcaseVertical} schema={showcaseSpec} defaultProps={sampleShowcase}
      width={1080} height={1920} fps={FPS} durationInFrames={300} calculateMetadata={showcaseMeta} />
    <Composition id="showcase-landscape" component={ShowcaseLandscape} schema={showcaseSpec} defaultProps={sampleShowcase}
      width={1920} height={1080} fps={FPS} durationInFrames={300} calculateMetadata={showcaseMeta} />
    <Composition id="vertical" component={FeatureVertical} schema={spec} defaultProps={sample}
      width={1080} height={1920} fps={FPS} durationInFrames={300} calculateMetadata={meta} />
    <Composition id="landscape" component={FeatureLandscape} schema={spec} defaultProps={sample}
      width={1920} height={1080} fps={FPS} durationInFrames={300} calculateMetadata={meta} />
    <Composition id="square" component={FeatureSquare} schema={spec} defaultProps={sample}
      width={1080} height={1080} fps={FPS} durationInFrames={300} calculateMetadata={meta} />
    <Still id="post" component={(p: StillSpec) => <SocialStill {...p} layout="post" />} schema={stillSpec}
      defaultProps={sampleStill} width={1080} height={1350} />
    <Still id="cover" component={Cover} schema={coverSpec}
      defaultProps={{ brand: "example", theme: "light", title: "Say what it does.", eyebrow: "", sub: "", footer: "", imageLabel: "", imageX: 0, imageY: 0 } as CoverSpec} width={1920} height={1080} />
    <Still id="og" component={(p: StillSpec) => <SocialStill {...p} layout="og" />} schema={stillSpec}
      defaultProps={sampleStill} width={1200} height={630} />
  </>
);

registerRoot(Root);
