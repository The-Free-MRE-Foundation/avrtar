using UnityEngine;
using UnityEditor;
using System;
using System.IO;
using VRC.SDKBase.Editor;
using VRC.SDK3.Builder;
using VRC.Core;
using VRCSDK2;
using System.Threading.Tasks;

public static class CommandLine
{
    public static string root = "";
    public static string email = "";
    public static string username = "";

    static CommandLine()
    {
        string[] args = System.Environment.GetCommandLineArgs();
        for (int i = 1; i < args.Length; ++i)
        {
            switch (args[i])
            {
                case "-email":
                    email = args[++i];
                    break;
                case "-username":
                    username = args[++i];
                    break;
                case "-root":
                    root = args[++i];
                    break;
                default:
                    if (!HandleUnityArgument(args, ref i))
                        Debug.Log($"Unknown command-line argument {args[i]}");
                    break;
            }
        }
    }

    static bool HandleUnityArgument(string[] args, ref int i)
    {
        switch (args[i].ToLower())
        {
            // Switches (no value)
            case "-batchmode":
            case "-nographics":
            case "-quit":
            case "-usehub":
            case "-hubipc":
            case "-skipupgradedialogs":
                return true;

            // Single value
            case "-logfile":
            case "-executemethod":
            case "-projectpath":
            case "-hubsessionid":
            case "-cloudenvironment":
                ++i;
                return true;
        }

        // Unsupported argument (if you hit this point, just add the argument to the appropriate
        // place above)
        return false;
    }
}

[InitializeOnLoad]
[ExecuteInEditMode]
public class upload : Editor
{
    public static String parentFolder = "Assets/Resources";
    private static byte[] _sigFileAsBytes;
    private static byte[] _fileAsBytes;

    [MenuItem("AVR2VRC/Auto Upload", false, 30)]
    public static async Task AutoUpload()
    {
        String email = CommandLine.email;
        if (String.IsNullOrEmpty(email))
        {
            email = "youremail";
        }
        String username = CommandLine.username;
        if (String.IsNullOrEmpty(username))
        {
            username = "yourusername";
        }
        String root = CommandLine.root;
        if (String.IsNullOrEmpty(root))
        {
            root = "yourrootdirectory";
        }

        // Build folder structure
        String emailFolder = Path.Combine(parentFolder, email);
        if (!AssetDatabase.IsValidFolder(emailFolder))
        {
            AssetDatabase.CreateFolder(parentFolder, email);
        }
        String modelFolder = Path.Combine(emailFolder, username);
        if (!AssetDatabase.IsValidFolder(modelFolder))
        {
            AssetDatabase.CreateFolder(emailFolder, username);
        }

        // Import fbx and change settings
        String modelFileName = username + ".fbx";
        String importPath = Path.Combine(modelFolder, modelFileName);
        Debug.Log(importPath);
        if (!File.Exists(importPath))
        {
            FileUtil.CopyFileOrDirectory(Path.Combine(root, email, modelFileName), importPath);
            AssetDatabase.ImportAsset(importPath);
            ModelImporter importer = AssetImporter.GetAtPath(importPath) as ModelImporter;
            importer.animationType = ModelImporterAnimationType.Human;
            importer.isReadable = true;
            importer.ExtractTextures(modelFolder);
            EditorUtility.SetDirty(importer);
            AssetDatabase.SaveAssets();
            AssetDatabase.Refresh();
        }

        // Import fbx into scene and hide limbs
        GameObject obj = (GameObject)PrefabUtility.InstantiatePrefab(Resources.Load(Path.Combine(email, username, username)));
        Transform limbs = obj.transform.Find("Limbs");
        limbs.gameObject.SetActive(false);

        // Build and upload
        VRC_SdkBuilder.shouldBuildUnityPackage = true;
        VRCAvatarBuilder builder = new VRCAvatarBuilder();
        VRC.SDK3.Avatars.Components.VRCAvatarDescriptor descriptor = obj.AddComponent<VRC.SDK3.Avatars.Components.VRCAvatarDescriptor>();
        PipelineManager component = descriptor.gameObject.AddComponent<PipelineManager>();
        // builder.ExportAndTestAvatarBlueprint(obj);
        builder.ExportAndUploadAvatarBlueprint(obj);
    }

    [RuntimeInitializeOnLoadMethod]
    static async void OnRuntimeMethodLoad()
    {
        Debug.Log("RuntimeMethodLoad: After first Scene loaded");
        await WaitUntil(() => GameObject.Find("VRCSDK") != null);
        GameObject sdk = GameObject.Find("VRCSDK");
        var rbc = sdk.GetComponent<RuntimeBlueprintCreation>();
        await WaitUntil(() => rbc.apiAvatar != null);
        rbc.blueprintName.text = "nameofyouravatar";
        rbc.blueprintDescription.text = "Altspace Avatar of " + "yourusername";
        rbc.uploadButton.onClick.Invoke();
        await WaitUntil(() => rbc.pipelineManager.completedSDKPipeline);
        if (Application.isBatchMode)
            EditorApplication.Exit(0);
        Debug.Log("Done");
    }

    public static async Task WaitUntil(Func<bool> condition, int frequency = 25, int timeout = -1)
    {
        var waitTask = Task.Run(async () =>
        {
            while (!condition()) await Task.Delay(frequency);
        });

        if (waitTask != await Task.WhenAny(waitTask,
                Task.Delay(timeout)))
            throw new TimeoutException();
    }
}