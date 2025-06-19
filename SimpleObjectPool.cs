using UnityEngine;
using System.Collections.Generic;

public class SimpleObjectPool : MonoBehaviour
{
    public GameObject prefabToPool;
    private List<GameObject> pooledObjects = new List<GameObject>();
    private GameObject poolContainer; // Parent for pooled objects to keep hierarchy clean

    void Awake()
    {
        // Ensure a container exists for organization
        poolContainer = new GameObject(prefabToPool.name + "_PoolContainer");
        poolContainer.transform.SetParent(this.transform);
    }

    public void Prewarm(GameObject prefab, int initialCount)
    {
        prefabToPool = prefab;
        if (prefabToPool == null)
        {
            Debug.LogError("Prefab to pool is null. Cannot prewarm.", this);
            return;
        }

        if (poolContainer == null) // Ensure container is set up, especially if Prewarm is called before Awake
        {
            poolContainer = new GameObject(prefabToPool.name + "_PoolContainer");
            poolContainer.transform.SetParent(this.transform);
        }

        for (int i = 0; i < initialCount; i++)
        {
            GameObject obj = Instantiate(prefabToPool);
            obj.transform.SetParent(poolContainer.transform); // Keep hierarchy clean
            obj.SetActive(false);
            pooledObjects.Add(obj);
        }
        Debug.Log($"Prewarmed pool for {prefabToPool.name} with {initialCount} instances.", this);
    }

    public GameObject Get()
    {
        if (prefabToPool == null)
        {
            Debug.LogError("Prefab to pool is null. Cannot Get object.", this);
            return null;
        }

        // Find an inactive object in the pool
        foreach (GameObject obj in pooledObjects)
        {
            if (!obj.activeInHierarchy)
            {
                obj.SetActive(true);
                return obj;
            }
        }

        // If no inactive object is found, instantiate a new one (and add to pool)
        Debug.LogWarning($"Pool for {prefabToPool.name} is empty or all objects are active. Instantiating a new one.", this);
        GameObject newObj = Instantiate(prefabToPool);
        newObj.transform.SetParent(poolContainer.transform); // Keep hierarchy clean
        pooledObjects.Add(newObj); // Add to pool for future use
        newObj.SetActive(true);
        return newObj;
    }

    public void Return(GameObject obj)
    {
        if (obj == null)
        {
            Debug.LogWarning("Tried to return a null object to the pool.", this);
            return;
        }

        // It's good practice to ensure the object being returned belongs to this pool's prefab type,
        // but for simplicity, we'll just deactivate it.
        // A more robust pool would check obj.GetComponent<SomeIdentifier>() or obj.name.Contains(prefabToPool.name)

        obj.SetActive(false);
        // Optionally, can add it back to pooledObjects list if it was an "overflow" object created at runtime
        // For this simple pool, if Get() created it, it's already added.
        // If the object was not originally from the pool and is being returned, ensure it's parented correctly.
        if (!pooledObjects.Contains(obj))
        {
             Debug.LogWarning($"Returning object {obj.name} which was not originally in the pool or was removed. Adding it and reparenting.", this);
             obj.transform.SetParent(poolContainer.transform);
             pooledObjects.Add(obj);
        }
    }
}
