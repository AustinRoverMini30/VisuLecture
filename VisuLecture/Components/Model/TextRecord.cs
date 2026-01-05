namespace VisuLecture.Components.Model;

public class TextRecord
{
    public string Text
    {
        get => _text;
        set => _text = value ?? throw new ArgumentNullException(nameof(value));
    }

    public string FilePath
    {
        get => _filePath;
        set => _filePath = value ?? throw new ArgumentNullException(nameof(value));
    }

    public string Name
    {
        get => _name;
        set => _name = value ?? throw new ArgumentNullException(nameof(value));
    }

    public string Id
    {
        get => _id;
        set => _id = value;
    }

    private string _text;
    private string _filePath;
    private string _name = "Untitled";
    private string _id;
    
    public TextRecord(string text, string filePath, string name, string id)
    {
        _text = text;
        _filePath = filePath;
        _name = name;
        _id = id;
    }
}