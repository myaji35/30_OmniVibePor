import { Config } from '@remotion/cli/config';

Config.setVideoImageFormat('jpeg');
Config.setCodec('h264');
Config.setConcurrency(1);
Config.setOverwriteOutput(true);

// Enable multi-process on Linux for faster rendering
Config.setEnableMultiProcessOnLinux(true);

// Increase timeout for longer videos
Config.setTimeout(120000); // 2 minutes
