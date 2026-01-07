namespace VisuLecture.Components.Model;

public class Theme
{
    public Theme()
    {
        Id = 0;
        Name = "";
        FolderName = "";
    }

    public Theme(int id, string name, string folderName)
    {
        Id = id;
        Name = name;
        FolderName = folderName;
    }

    public int Id { get; set; }
    public string Name { get; set; } = "";
    public string FolderName { get; set; } = ""; // Nom du dossier dans wwwroot/pictures/themes/
}

