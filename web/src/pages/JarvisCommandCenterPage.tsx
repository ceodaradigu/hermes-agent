import { useEffect, useMemo, useState } from "react";
import { api, type JarvisDashboardStatus } from "@/lib/api";
import { fallbackDashboard, type CommandCenterTabId } from "@/components/jarvis/contracts";
import { JarvisPresenceShell } from "@/components/jarvis/JarvisPresenceShell";
import { useJarvisAudioRecorder } from "@/hooks/jarvis/useJarvisAudioRecorder";
import { useJarvisCameraControl } from "@/hooks/jarvis/useJarvisCameraControl";
import { useJarvisEventStream } from "@/hooks/jarvis/useJarvisEventStream";
import { useLocalVoiceLoop } from "@/hooks/jarvis/useLocalVoiceLoop";

export default function JarvisCommandCenterPage() {
  const [dashboard, setDashboard] = useState<JarvisDashboardStatus>(() => fallbackDashboard("loading"));
  const [connectionState, setConnectionState] = useState<"loading" | "online" | "offline">("loading");
  const [activeTab, setActiveTab] = useState<CommandCenterTabId>("cockpit");
  const localVoice = useLocalVoiceLoop();
  const cameraControl = useJarvisCameraControl();
  const audioRecorder = useJarvisAudioRecorder();
  const localSensors = useMemo(() => ({
    camera: {
      state: cameraControl.cameraState,
      active: cameraControl.cameraActive,
      auditEvents: cameraControl.cameraAuditEvents,
      videoRecordingState: cameraControl.videoRecordingState,
      videoRecordingActive: cameraControl.videoRecordingActive,
      videoRecording: cameraControl.videoRecording,
    },
    recording: {
      state: audioRecorder.recordingState,
      active: audioRecorder.recordingActive,
      recording: audioRecorder.recording,
      auditEvents: audioRecorder.recordingAuditEvents,
    },
  }), [
    audioRecorder.recording,
    audioRecorder.recordingActive,
    audioRecorder.recordingAuditEvents,
    audioRecorder.recordingState,
    cameraControl.cameraActive,
    cameraControl.cameraAuditEvents,
    cameraControl.cameraState,
    cameraControl.videoRecording,
    cameraControl.videoRecordingActive,
    cameraControl.videoRecordingState,
  ]);
  const eventStream = useJarvisEventStream(dashboard, localSensors);

  useEffect(() => {
    let active = true;
    api.getJarvisDashboardStatus()
      .then((payload) => {
        if (!active) return;
        setDashboard(payload);
        setConnectionState("online");
      })
      .catch(() => {
        if (!active) return;
        setDashboard(fallbackDashboard("offline"));
        setConnectionState("offline");
      });
    return () => {
      active = false;
    };
  }, []);

  return (
    <JarvisPresenceShell
      dashboard={dashboard}
      connectionState={connectionState}
      activeTab={activeTab}
      onTabChange={setActiveTab}
      localVoice={localVoice}
      cameraControl={cameraControl}
      audioRecorder={audioRecorder}
      events={eventStream.events}
      eventConnectionState={eventStream.connectionState}
    />
  );
}
